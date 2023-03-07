"""Proactor implementation"""

import asyncio
import enum
import functools
import json
import sys
import time
import traceback
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Awaitable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence

import gwproto
from gwproto import MQTTCodec
from gwproto.messages import Ack
from gwproto.messages import CommEvent
from gwproto.messages import EventBase
from gwproto.messages import EventT
from gwproto.messages import MQTTConnectEvent
from gwproto.messages import MQTTDisconnectEvent
from gwproto.messages import MQTTFullySubscribedEvent
from gwproto.messages import PeerActiveEvent
from gwproto.messages import Ping
from gwproto.messages import PingMessage
from gwproto.messages import ProblemEvent
from gwproto.messages import ResponseTimeoutEvent
from gwproto.messages import ShutdownEvent
from gwproto.messages import StartupEvent
from paho.mqtt.client import MQTTMessageInfo
from result import Err
from result import Ok
from result import Result

from gwproactor.config.proactor_settings import MQTT_LINK_POLL_SECONDS
from gwproactor.message import DBGCommands
from gwproactor.message import DBGEvent
from gwproactor.message import DBGPayload
from problems import Problems
from gwproactor import config
from gwproactor import ProactorSettings
from gwproactor.link_state import LinkStates
from gwproactor.link_state import Transition
from gwproactor.logger import ProactorLogger
from gwproactor.message import Message
from gwproactor.message import MQTTConnectFailPayload
from gwproactor.message import MQTTConnectPayload
from gwproactor.message import MQTTDisconnectPayload
from gwproactor.message import MQTTProblemsPayload
from gwproactor.message import MQTTReceiptPayload
from gwproactor.message import MQTTSubackPayload
from gwproactor.message import PatWatchdog
from gwproactor.message import Shutdown
from gwproactor.mqtt import MQTTClients
from gwproactor.mqtt import QOS
from gwproactor.persister import JSONDecodingError
from gwproactor.persister import PersisterInterface
from gwproactor.persister import StubPersister
from gwproactor.persister import UIDMissingWarning
from gwproactor.proactor_interface import CommunicatorInterface
from gwproactor.proactor_interface import MonitoredName
from gwproactor.proactor_interface import Runnable
from gwproactor.proactor_interface import ServicesInterface
from gwproactor.stats import ProactorStats
from gwproactor.watchdog import WatchdogManager


@dataclass
class AckWaitInfo:
    message_id: str
    timer_handle: asyncio.TimerHandle
    client_name: str
    context: Any = None


class AckWaitSummary(enum.Enum):
    acked = "acked"
    timeout = "timeout"
    connection_failure = "connection_failure"


@dataclass
class AckWaitResult:
    summary: AckWaitSummary
    wait_info: AckWaitInfo

    def __bool__(self) -> bool:
        return self.ok()

    def ok(self) -> bool:
        return self.summary == AckWaitSummary.acked


import_time = time.time()

@dataclass
class MessageTimes:
    last_send: float = field(default_factory=time.time)
    last_recv: float = field(default_factory=time.time)

    def next_ping_second(self, link_poll_seconds: float) -> float:
        return self.last_send + link_poll_seconds

    def seconds_until_next_ping(self, link_poll_seconds: float) -> float:
        return self.next_ping_second(link_poll_seconds) - time.time()

    def time_to_send_ping(self, link_poll_seconds: float) -> bool:
        return time.time() > self.next_ping_second(link_poll_seconds)

    def get_str(self, link_poll_seconds: float = MQTT_LINK_POLL_SECONDS, relative: bool = True) -> str:
        if relative:
            adjust = import_time
        else:
            adjust = 0
        return (
            f"n:{time.time() - adjust:5.2f}  lps:{link_poll_seconds:5.2f}  "
            f"ls:{self.last_send - adjust:5.2f}  lr:{self.last_recv - adjust:5.2f}  "
            f"nps:{self.next_ping_second(link_poll_seconds) - adjust:5.2f}  "
            f"snp:{self.next_ping_second(link_poll_seconds):5.2f}  "
            f"tsp:{int(self.time_to_send_ping(link_poll_seconds))}"
        )

    def __str__(self) -> str:
        return self.get_str()

class Proactor(ServicesInterface, Runnable):

    PERSISTER_ENCODING = "utf-8"

    _name: str
    _settings: ProactorSettings
    _logger: ProactorLogger
    _stats: ProactorStats
    _event_persister: PersisterInterface
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _receive_queue: Optional[asyncio.Queue] = None
    _mqtt_clients: MQTTClients
    _mqtt_codecs: Dict[str, MQTTCodec]
    _link_states: LinkStates
    _link_message_times: dict[str, MessageTimes]
    _acks: dict[str, AckWaitInfo]
    _communicators: Dict[str, CommunicatorInterface]
    _stop_requested: bool
    _tasks: List[asyncio.Task]
    _watchdog: WatchdogManager

    def __init__(self, name: str, settings: ProactorSettings):
        self._name = name
        self._settings = settings
        self._logger = ProactorLogger(**settings.logging.qualified_logger_names())
        self._stats = self.make_stats()
        self._event_persister = self.make_event_persister(settings)
        self._mqtt_clients = MQTTClients()
        self._mqtt_codecs = dict()
        self._link_states = LinkStates()
        self._link_message_times = dict()
        self._acks = dict()
        self._communicators = dict()
        self._tasks = []
        self._stop_requested = False
        self._watchdog = WatchdogManager(10, self)
        self.add_communicator(self._watchdog)

    @classmethod
    def make_stats(cls) -> ProactorStats:
        return ProactorStats()

    @classmethod
    def make_event_persister(cls, settings:ProactorSettings) -> PersisterInterface:
        return StubPersister()

    def send(self, message: Message):
        if not isinstance(message.Payload, PatWatchdog):
            self._logger.message_summary(
                "OUT internal",
                message.Header.Src,
                f"{message.Header.Dst}/{message.Header.MessageType}",
                message.Payload,
            )
        self._receive_queue.put_nowait(message)

    def send_threadsafe(self, message: Message) -> None:
        self._loop.call_soon_threadsafe(self._receive_queue.put_nowait, message)

    def get_communicator(self, name: str) -> CommunicatorInterface:
        return self._communicators[name]

    @property
    def name(self) -> str:
        return self._name

    @property
    def publication_name(self) -> str:
        return self._name

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return []

    @property
    def settings(self) -> ProactorSettings:
        return self._settings

    @property
    def logger(self) -> ProactorLogger:
        return self._logger

    @property
    def stats(self) -> ProactorStats:
        return self._stats

    @property
    def upstream_client(self) -> str:
        return self._mqtt_clients.upstream_client

    @property
    def primary_peer_client(self) -> str:
        return self._mqtt_clients.primary_peer_client

    def _send(self, message: Message):
        self.send(message)

    def generate_event(self, event: EventT) -> Result[bool, BaseException]:
        if isinstance(event, CommEvent):
            self.stats.link(event.PeerName).comm_event_counts[event.TypeName] += 1
        if isinstance(event, ProblemEvent) and self.logger.path_enabled:
            self.logger.info(event)
        if not event.Src:
            event.Src = self.publication_name
        if self._mqtt_clients.upstream_client and self._link_states[self._mqtt_clients.upstream_client].active_for_send():
            self._publish_upstream(event, AckRequired=True)
        return self._event_persister.persist(event.MessageId, event.json(
            sort_keys=True, indent=2).encode(self.PERSISTER_ENCODING))

    def _add_mqtt_client(
        self,
        name: str,
        client_config: config.MQTTClient,
        codec: Optional[MQTTCodec] = None,
        upstream: bool = False,
        primary_peer: bool = False,
    ):
        self._mqtt_clients.add_client(name, client_config, upstream=upstream, primary_peer=primary_peer)
        if codec is not None:
            self._mqtt_codecs[name] = codec
        self._link_states.add(name)
        self._link_message_times[name] = MessageTimes()
        self._stats.add_link(name)

    async def _send_ping(self, client: str):
        while not self._stop_requested:
            message_times = self._link_message_times[client]
            link_state = self._link_states[client]
            if message_times.time_to_send_ping(self.settings.mqtt_link_poll_seconds) and link_state.active_for_send():
                self._publish_message(client, PingMessage(Src=self.publication_name))
            await asyncio.sleep(message_times.seconds_until_next_ping(self.settings.mqtt_link_poll_seconds))

    def _start_ack_timer(self, client_name: str, message_id: str, context: Any = None, delay: Optional[float] = None) -> None:
        if delay is None:
            delay = 5
        self._acks[message_id] = AckWaitInfo(
            message_id,
            asyncio.get_running_loop().call_later(
                delay,
                functools.partial(self._process_ack_timeout, message_id),
            ),
            client_name=client_name,
            context=context,
        )

    def _cancel_ack_timer(self, message_id: str) -> Optional[AckWaitInfo]:
        self._logger.path("++cancel_ack_timer %s", message_id)
        path_dbg = 0
        wait_info = self._acks.pop(message_id, None)
        if wait_info is not None:
            path_dbg |= 0x00000001
            wait_info.timer_handle.cancel()

        self._logger.path("--cancel_ack_timer path:0x%08X", path_dbg)
        return wait_info

    def _process_ack_timeout(self, message_id: str):
        self._logger.message_enter("++Proactor._process_ack_timeout %s", message_id)
        wait_info = self._acks.get(message_id, None)
        if wait_info is not None:
            self.stats.link(wait_info.client_name).timeouts += 1
        self._process_ack_result(message_id, AckWaitSummary.timeout)
        self._logger.message_exit("--Proactor._process_ack_timeout")

    def _apply_ack_timeout(self, transition: Transition) -> Ok:
        self._logger.path("++Proactor._apply_ack_timeout")
        path_dbg = 0
        if transition.deactivated():
            path_dbg |= 0x00000001
            self.generate_event(ResponseTimeoutEvent(PeerName=transition.link_name))
            self._logger.comm_event(str(transition))
            if transition.recv_deactivated():
                path_dbg |= 0x00000002
                self._derived_recv_deactivated(transition)
                for message_id in list(self._acks.keys()):
                    path_dbg |= 0x00000004
                    self._process_ack_result(message_id, AckWaitSummary.connection_failure)
        self._logger.path("--Proactor._apply_ack_timeout path:0x%08X", path_dbg)
        return Ok()

    def _process_ack_result(self, message_id: str, reason: AckWaitSummary):
        self._logger.path("++Proactor._process_ack_result  %s", message_id)
        path_dbg = 0
        wait_info = self._cancel_ack_timer(message_id)
        if wait_info is not None:
            path_dbg |= 0x00000001
            if reason == AckWaitSummary.timeout:
                path_dbg |= 0x00000002
                self._link_states.process_ack_timeout(
                    wait_info.client_name
                ).and_then(
                    self._apply_ack_timeout
                ).or_else(
                    self._report_error
                )
            elif reason == AckWaitSummary.acked and message_id in self._event_persister:
                path_dbg |= 0x00000004
                self._event_persister.clear(message_id)
        self._logger.path("--Proactor._process_ack_result path:0x%08X", path_dbg)

    def _process_dbg(self, dbg: DBGPayload):
        self._logger.path("++_process_dbg")
        path_dbg = 0
        count_dbg = 0
        for logger_name in ["message_summary", "lifecycle", "comm_event"]:
            requested_level = getattr(dbg.Levels, logger_name)
            if requested_level > -1:
                path_dbg |= 0x00000001
                count_dbg += 1
                logger = getattr(self._logger, logger_name + "_logger")
                old_level = logger.getEffectiveLevel()
                logger.setLevel(requested_level)
                self._logger.debug(
                    "%s logger level %s -> %s",
                    logger_name,
                    old_level,
                    logger.getEffectiveLevel()
                )
        match dbg.Command:
            case DBGCommands.show_subscriptions:
                path_dbg |= 0x00000002
                self.log_subscriptions("message")
            case _:
                path_dbg |= 0x00000004
        self.generate_event(DBGEvent(Command=dbg, Path=f"0x{path_dbg:08X}", Count=count_dbg, Msg=""))
        self._logger.path("--_process_dbg  path:0x%08X  count:%d", path_dbg, count_dbg)

    def log_subscriptions(self, tag=""):
        if self._logger.lifecycle_enabled:
            s = f"Scada2 subscriptions: [{tag}]]\n"
            for client in self._mqtt_clients.clients:
                s += f"\t{client}\n"
                for subscription in self._mqtt_clients.client_wrapper(client).subscription_items():
                    s += f"\t\t[{subscription}]\n"
            self._logger.lifecycle(s)

    def _publish_message(self, client, message: Message, qos: int = 0, context: Any = None) -> MQTTMessageInfo:
        topic = message.mqtt_topic()
        payload = self._mqtt_codecs[client].encode(message)
        self._logger.message_summary("OUT mqtt    ", message.Header.Src, topic, message.Payload)
        if message.Header.AckRequired:
            if message.Header.MessageId in self._acks:
                self._cancel_ack_timer(message.Header.MessageId)
            self._start_ack_timer(client, message.Header.MessageId, context)
        self._link_message_times[client].last_send = time.time()
        return self._mqtt_clients.publish(client, topic, payload, qos)

    def _publish_upstream(
        self, payload, qos: QOS = QOS.AtMostOnce, **message_args: Any
    ) -> MQTTMessageInfo:
        message = Message(Src=self.publication_name, Payload=payload, **message_args)
        return self._publish_message(self._mqtt_clients.upstream_client, message, qos=qos)


    def add_communicator(self, communicator: CommunicatorInterface):
        if communicator.name in self._communicators:
            raise ValueError(
                f"ERROR. Communicator with name [{communicator.name}] already present"
            )
        self._communicators[communicator.name] = communicator
        for monitored in communicator.monitored_names:
            self._watchdog.add_monitored_name(monitored)

    @property
    def async_receive_queue(self) -> Optional[asyncio.Queue]:
        return self._receive_queue

    @property
    def event_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._loop

    async def process_messages(self):
        # noinspection PyBroadException
        try:
            self._start_processing_messages()
            while not self._stop_requested:
                message = await self._receive_queue.get()
                if not self._stop_requested:
                    await self.process_message(message)
                self._receive_queue.task_done()
        except BaseException as e:
            if not isinstance(e, asyncio.exceptions.CancelledError):
                self._logger.exception(f"ERROR in process_message")
                self._logger.error("Stopping proactor")
                # noinspection PyBroadException
                try:
                    self.generate_event(
                        ShutdownEvent(
                            Reason=(
                                f"ERROR in process_message {e}\n"
                                f"{traceback.format_exception(e)}"
                            )
                        )
                    )
                except:
                    self._logger.exception(f"ERROR generating exception event")
        # noinspection PyBroadException
        try:
            self.stop()
        except:
            self._logger.exception(f"ERROR stopping proactor")

    def start_tasks(self):
        self._tasks = [
            asyncio.create_task(self.process_messages(), name="process_messages"),
        ]
        for link in self._link_message_times:
            self._tasks.append(asyncio.create_task(self._send_ping(link)))
        self._start_derived_tasks()

    def _start_derived_tasks(self):
        pass

    def _derived_process_message(self, message: Message):
        pass

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        pass

    @classmethod
    def _second_caller(cls) -> str:
        try:
            # noinspection PyProtectedMember,PyUnresolvedReferences
            return sys._getframe(2).f_back.f_code.co_name
        except BaseException as e:
            return f"[ERROR extracting caller of _report_errors: {e}"

    def _report_error(self, error: BaseException, msg: str = "") -> Result[bool, BaseException]:
        try:
            if not msg:
                msg = self._second_caller()
            self._report_errors([error], msg)
        except BaseException as e2:
            return Err(e2)
        return Ok()

    def _report_errors(self, errors: Sequence[BaseException], msg: str = "") -> Result[bool, BaseException]:
        try:
            if not msg:
                msg = self._second_caller()
            self.generate_event(Problems(errors=errors).problem_event(msg))
        except BaseException as e2:
            return Err(e2)
        return Ok()

    def _start_processing_messages(self):
        """Processing before any messages are pulled from queue"""
        self.generate_event(StartupEvent())
        self._link_states.start_all().or_else(self._report_errors)

    async def process_message(self, message: Message):
        if not isinstance(message.Payload, PatWatchdog):
            self._logger.message_enter("++Proactor.process_message %s/%s",
                                       message.Header.Src, message.Header.MessageType)
        path_dbg = 0
        if not isinstance(message.Payload, (MQTTReceiptPayload, PatWatchdog)):
            path_dbg |= 0x00000001
            self._logger.message_summary(
                "IN  internal",
                self.name,
                f"{message.Header.Src}/{message.Header.MessageType}",
                message.Payload,
            )
        self._stats.add_message(message)
        match message.Payload:
            case MQTTReceiptPayload():
                path_dbg |= 0x00000002
                self._process_mqtt_message(message)
            case MQTTConnectPayload():
                path_dbg |= 0x00000004
                self._process_mqtt_connected(message)
            case MQTTDisconnectPayload():
                path_dbg |= 0x00000008
                self._process_mqtt_disconnected(message)
            case MQTTConnectFailPayload():
                path_dbg |= 0x00000010
                self._process_mqtt_connect_fail(message)
            case MQTTSubackPayload():
                path_dbg |= 0x00000020
                self._process_mqtt_suback(message)
            case MQTTProblemsPayload():
                path_dbg |= 0x00000040
                self._process_mqtt_problems(message)
            case PatWatchdog():
                path_dbg |= 0x00000080
                self._watchdog.process_message(message)
            case Shutdown():
                path_dbg |= 0x00000100
                self._process_shutdown_message(message)
            case EventBase():
                path_dbg |= 0x00000200
                self.generate_event(message.Payload)
            case _:
                path_dbg |= 0x00000400
                self._derived_process_message(message)
        if not isinstance(message.Payload, PatWatchdog):
            self._logger.message_exit("--Proactor.process_message  path:0x%08X", path_dbg)

    def _decode_mqtt_message(self, mqtt_payload) -> Result[Message[Any], BaseException]:
        decoder = self._mqtt_codecs.get(mqtt_payload.client_name, None)
        result: Result[Message[Any], BaseException]
        try:
            result = Ok(decoder.decode(mqtt_payload.message.topic, mqtt_payload.message.payload))
        except Exception as e:
            self._logger.exception("ERROR decoding [%s]", mqtt_payload)
            self.generate_event(
                ProblemEvent(
                    ProblemType=gwproto.messages.Problems.warning,
                    Summary=f"Decoding error topic [{mqtt_payload.message.topic}]  error [{type(e)}]",
                    Details=(
                        f"Topic: {mqtt_payload.message.topic}\n"
                        f"Message: {mqtt_payload.message.payload[:70]}"
                        f"{'...' if len(mqtt_payload.message.payload)> 70 else ''}\n"
                        f"{traceback.format_exception(e)}\n"
                        f"Exception: {e}"
                    )
                )
            )
            result = Err(e)
        return result

    def _process_mqtt_message(self, mqtt_receipt_message: Message[MQTTReceiptPayload]) -> Result[Message[Any], BaseException]:
        self._logger.path("++Proactor._process_mqtt_message %s/%s",
                          mqtt_receipt_message.Header.Src, mqtt_receipt_message.Header.MessageType)
        path_dbg = 0
        self._stats.add_mqtt_message(mqtt_receipt_message)
        match result := self._decode_mqtt_message(mqtt_receipt_message.Payload):
            case Ok(decoded_message):
                path_dbg |= 0x00000002
                self._logger.message_summary("IN  mqtt    ", self.name,
                                             mqtt_receipt_message.Payload.message.topic, decoded_message.Payload)
                match self._link_states.process_mqtt_message(mqtt_receipt_message):
                    case Ok(transition):
                        path_dbg |= 0x00000004
                        self._link_message_times[mqtt_receipt_message.Payload.client_name].last_recv = time.time()
                        if transition:
                            self._logger.comm_event(transition)
                        if transition.recv_activated():
                            path_dbg |= 0x00000008
                            self._recv_activated(transition)
                        elif transition.recv_deactivated():
                            path_dbg |= 0x00000010
                            self._derived_recv_deactivated(transition)
                    case Err(error):
                        path_dbg |= 0x00000020
                        self._report_error(error, "_process_mqtt_message/_link_states.process_mqtt_message")
                match decoded_message.Payload:
                    case Ack():
                        path_dbg |= 0x00000040
                        self._process_ack_result(decoded_message.Payload.AckMessageID, AckWaitSummary.acked)
                    case Ping():
                        path_dbg |= 0x00000080
                    case DBGPayload():
                        path_dbg |= 0x00000100
                        self._process_dbg(decoded_message.Payload)
                    case _:
                        path_dbg |= 0x00000200
                        self._derived_process_mqtt_message(mqtt_receipt_message, decoded_message)
                if decoded_message.Header.AckRequired:
                    path_dbg |= 0x00000400
                    if decoded_message.Header.MessageId:
                        path_dbg |= 0x00000800
                        self._publish_message(
                            mqtt_receipt_message.Payload.client_name,
                            Message(
                                Src=self.publication_name,
                                Payload=Ack(AckMessageID=decoded_message.Header.MessageId)
                            )
                        )
            case Err(error):
                path_dbg |= 0x00001000
                result = Err(error)
        self._logger.path("--Proactor._process_mqtt_message:%s  path:0x%08X", int(result.is_ok()), path_dbg)
        return result

    def _process_mqtt_connected(self, message: Message[MQTTConnectPayload]):
        match self._link_states.process_mqtt_connected(message):
            case Ok(transition):
                self._logger.comm_event(transition)
            case Err(error):
                self._report_error(error, "_process_mqtt_connected")
        self.generate_event(MQTTConnectEvent(PeerName=message.Payload.client_name))
        self._mqtt_clients.subscribe_all(message.Payload.client_name)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def _derived_recv_deactivated(self, transition: Transition) -> Result[bool, BaseException]:
        return Ok()

    def _recv_activated(self, transition: Transition) -> Result[bool, BaseException]:
        self.generate_event(PeerActiveEvent(PeerName=transition.link_name))
        self._upload_pending_events()
        self._derived_recv_activated(transition)
        return Ok()

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def _derived_recv_activated(self, transition: Transition) -> Result[bool, BaseException]:
        return Ok()

    def _process_mqtt_disconnected(self, message: Message[MQTTDisconnectPayload]) -> Result[bool, BaseException]:
        result: Result[bool, BaseException] = Ok()
        match self._link_states.process_mqtt_disconnected(message):
            case Ok(transition):
                self.generate_event(MQTTDisconnectEvent(PeerName=message.Payload.client_name))
                self._logger.comm_event(transition)
                if transition.recv_deactivated():
                    result = self._derived_recv_deactivated(transition)
                if transition.recv_deactivated() or transition.send_deactivated():
                    for message_id in list(self._acks.keys()):
                        self._process_ack_result(message_id, AckWaitSummary.connection_failure)
            case Err(error):
                result = Err(error)
        return result

    def _process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]) -> Result[bool, BaseException]:
        return self._link_states.process_mqtt_connect_fail(message)

    def _upload_pending_events(self) -> Result[bool, BaseException]:
        errors = []
        for message_id in self._event_persister.pending():
            match self._event_persister.retrieve(message_id):
                case Ok(event_bytes):
                    if event_bytes is None:
                        errors.append(UIDMissingWarning("_upload_pending_events", uid=message_id))
                    else:
                        try:
                            event = json.loads(event_bytes.decode(encoding=self.PERSISTER_ENCODING))
                        except BaseException as e:
                            errors.append(e)
                            errors.append(JSONDecodingError("_upload_pending_events", uid=message_id))
                        else:
                            self._publish_upstream(event, AckRequired=True)
                case Err(error):
                    errors.append(error)
        if errors:
            return Err(Problems(errors=errors))
        return Ok()

    def _process_mqtt_suback(self, message: Message[MQTTSubackPayload]) -> Result[bool, BaseException]:
        self._logger.path("++Proactor._process_mqtt_suback client:%s", message.Payload.client_name)
        path_dbg = 0

        result: Result[bool, BaseException] = Ok()
        match self._link_states.process_mqtt_suback(
            message.Payload.client_name,
            self._mqtt_clients.handle_suback(message.Payload)
        ):
            case Ok(transition):
                path_dbg |= 0x00000001
                if transition:
                    path_dbg |= 0x00000002
                    self._logger.comm_event(transition)
                if transition.send_activated():
                    path_dbg |= 0x00000004
                    self._upload_pending_events()
                    self.generate_event(MQTTFullySubscribedEvent(PeerName=message.Payload.client_name))
                    self._publish_message(
                        message.Payload.client_name,
                        PingMessage(Src=self.publication_name)
                    )
                if transition.recv_activated():
                    path_dbg |= 0x00000008
                    result = self._recv_activated(transition)
            case Err(error):
                path_dbg |= 0x00000010
                result = Err(error)
        self._logger.path(
            "--Proactor._process_mqtt_suback:%d  path:0x%08X",
            result.is_ok(),
            path_dbg,
        )
        return result

    def _process_mqtt_problems(self, message: Message[MQTTProblemsPayload]) -> Result[bool, BaseException]:
        self.generate_event(
            ProblemEvent(
                ProblemType=gwproto.messages.Problems.error,
                Summary=f"Error in mqtt event loop for client [{message.Payload.client_name}]",
                Details=(
                    f"{message.Payload.problems}\n"
                    f"{message.Payload.problems.error_traceback_str()}"
                )
            )
        )
        return Ok()

    def _process_shutdown_message(self, message:Message[Shutdown]):
        self._stop_requested = True
        self.generate_event(ShutdownEvent(Reason=message.Payload.Reason))
        self._logger.lifecycle(f"Shutting down due to ShutdownMessage, [{message.Payload.Reason}]")

    async def run_forever(self):
        self._loop = asyncio.get_running_loop()
        self._receive_queue = asyncio.Queue()
        self._mqtt_clients.start(self._loop, self._receive_queue)
        for communicator in self._communicators.values():
            if isinstance(communicator, Runnable):
                communicator.start()
        self.start_tasks()
        await self.join()

    def stop_mqtt(self):
        self._mqtt_clients.stop()

    def start(self):
        # TODO clean up this interface for proactor
        raise RuntimeError("ERROR. Proactor must be started by awaiting run_forever()")

    def stop(self):
        # TODO: CS - where does _link_states.stop() get called? never?
        self._stop_requested = True
        for task in self._tasks:
            # TODO: CS - Send self a shutdown message instead?
            if not task.done():
                task.cancel()
        self.stop_mqtt()
        for communicator in self._communicators.values():
            if isinstance(communicator, Runnable):
                # noinspection PyBroadException
                try:
                    communicator.stop()
                except:
                    pass

    async def join(self):
        self._logger.lifecycle("++Proactor.join()")
        self._logger.lifecycle(str_tasks(self._loop, "Proactor.join() - all tasks"))
        running: List[Awaitable] = self._tasks[:]
        for communicator in self._communicators.values():
            communicator_name = communicator.name
            if isinstance(communicator, Runnable):
                running.append(
                    self._loop.create_task(
                        communicator.join(), name=f"{communicator_name}.join"
                    )
                )
        # noinspection PyBroadException
        try:
            while running:
                self._logger.lifecycle(str_tasks(self._loop, "WAITING FOR", tasks=running))
                # if not isinstance(e, asyncio.exceptions.CancelledError):
                done, running = await asyncio.wait(running, return_when="FIRST_COMPLETED")
                self._logger.lifecycle(str_tasks(self._loop, tag="DONE", tasks=done))
                self._logger.lifecycle(str_tasks(self._loop, tag="PENDING", tasks=running))
                for task in done:
                    if not task.cancelled() and (exception := task.exception()):
                        self._logger.error(f"EXCEPTION in task {task.get_name()}  {exception}")
                        self._logger.error(traceback.format_tb(exception.__traceback__))
        except:
            self._logger.exception("ERROR in Proactor.join")
        self._logger.lifecycle("--Proactor.join()")

    def publish(self, client: str, topic: str, payload: bytes, qos: int):
        self._mqtt_clients.publish(client, topic, payload, qos)

def str_tasks(loop_: asyncio.AbstractEventLoop, tag: str = "", tasks: Optional[Iterable[Awaitable]] = None) -> str:
    s = ""
    try:
        if tasks is None:
            tasks = asyncio.all_tasks(loop_)
        s += f"Tasks: {len(tasks)}  [{tag}]\n"

        def _get_task_exception(task_):
            try:
                exception_ = task_.exception()
            except asyncio.CancelledError as _e:
                exception_ = _e
            except asyncio.InvalidStateError:
                exception_ = None
            return exception_

        for i, task in enumerate(tasks):
            s += (
                f"\t{i + 1}/{len(tasks)}  "
                f"{task.get_name():20s}  "
                f"done:{task.done()}   "
                f"exception:{_get_task_exception(task)}  "
                f"{task.get_coro()}\n"
            )
    except BaseException as e:
        # noinspection PyBroadException
        try:
            s += f"ERROR in str_tasks:\n"
            s += "".join(traceback.format_exception(e))
            s += "\n"
        except:
            pass
    return s
