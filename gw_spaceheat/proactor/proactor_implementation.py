"""Proactor implementation"""

import asyncio
import enum
import functools
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

import config
from proactor.link_state import LinkStates
from proactor.link_state import Transition
from proactor.logger import ProactorLogger
from proactor.message import Message
from proactor.message import MQTTConnectFailPayload
from proactor.message import MQTTConnectPayload
from proactor.message import MQTTDisconnectPayload
from proactor.message import MQTTReceiptPayload
from proactor.message import MQTTSubackPayload
from proactor.mqtt import MQTTClients
from proactor.proactor_interface import CommunicatorInterface
from proactor.proactor_interface import Runnable
from proactor.proactor_interface import ServicesInterface
from proactor.problems import Problems


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


LINK_POLL_SECONDS = 60


@dataclass
class MessageTimes:
    last_send: float = field(default_factory=time.time)
    last_recv: float = field(default_factory=time.time)

    def next_ping_second(self, link_poll_seconds: float) -> float:
        return self.last_send + link_poll_seconds

    def seconds_until_next_ping(self, link_poll_seconds: float) -> float:
        return self.next_ping_second(link_poll_seconds) - time.time()

    def time_to_send_ping(self, link_poll_seconds: float) -> bool:
        return time.time() > self.seconds_until_next_ping(link_poll_seconds)


class Proactor(ServicesInterface, Runnable):
    _name: str
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
    _logger: ProactorLogger

    def __init__(self, name: str, logger: ProactorLogger):
        self._name = name
        self._logger = logger
        self._mqtt_clients = MQTTClients()
        self._mqtt_codecs = dict()
        self._link_states = LinkStates()
        self._link_message_times = dict()
        self._acks = dict()
        self._communicators = dict()
        self._tasks = []
        self._stop_requested = False

    def _add_mqtt_client(
        self,
        name: str,
        client_config: config.MQTTClient,
        codec: Optional[MQTTCodec] = None,
    ):
        self._mqtt_clients.add_client(name, client_config)
        if codec is not None:
            self._mqtt_codecs[name] = codec
        self._link_states.add(name)
        self._link_message_times[name] = MessageTimes()

    async def _send_ping(self, client: str):
        while not self._stop_requested:
            message_times = self._link_message_times[client]
            link_state = self._link_states[client]
            if message_times.time_to_send_ping(LINK_POLL_SECONDS) and link_state.active_for_send():
                self._publish_message(client, PingMessage(Src=self.publication_name))
            await asyncio.sleep(message_times.seconds_until_next_ping(LINK_POLL_SECONDS))

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
            # self._logger.info(
            #     f"cancelling timer {wait_info.timer_handle}  {id(wait_info.timer_handle)}  "
            #     f"canceled? {wait_info.timer_handle.cancelled()}  "
            #     f"when:{wait_info.timer_handle.when()}"
            # )
            wait_info.timer_handle.cancel()
            # self._logger.info(
            #     f"canceled timer   {wait_info.timer_handle}  {id(wait_info.timer_handle)}  "
            #     f"canceled? {wait_info.timer_handle.cancelled()}  "
            #     f"when:{wait_info.timer_handle.when()}"
            # )

        self._logger.path("--cancel_ack_timer path:0x%08X", path_dbg)
        return wait_info

    def _process_ack_timeout(self, message_id: str):
        self._logger.message_enter("++Proactor._process_ack_timeout %s", message_id)
        self._process_ack_result(message_id, AckWaitSummary.timeout)
        self._logger.message_exit("--Proactor._process_ack_timeout")

    def _derived_process_ack_result(self, result: AckWaitResult):
        ...

    def _process_ack_result(self, message_id: str, reason: AckWaitSummary):
        self._logger.path("++Proactor._process_ack_result  %s", message_id)
        path_dbg = 0
        wait_info = self._cancel_ack_timer(message_id)
        if wait_info is not None:
            path_dbg |= 0x00000001
            if reason == AckWaitSummary.timeout:
                path_dbg |= 0x00000002
                result = self._link_states.process_ack_timeout(wait_info.client_name).or_else(self._report_error)
                match result:
                    case Ok(transition):
                        path_dbg |= 0x00000004
                        if transition.deactivated():
                            path_dbg |= 0x00000008
                            self.generate_event(ResponseTimeoutEvent(PeerName=wait_info.client_name))
                            self._logger.comm_event(transition)
                            if transition.recv_deactivated():
                                path_dbg |= 0x00000010
                                self._derived_recv_deactivated(transition).or_else(self._report_error)
                                for message_id in list(self._acks.keys()):
                                    path_dbg |= 0x00000020
                                    self._process_ack_result(message_id, AckWaitSummary.connection_failure)
            self._derived_process_ack_result(AckWaitResult(summary=reason, wait_info=wait_info))
        self._logger.path("--Proactor._process_ack_result path:0x%08X", path_dbg)

    # TODO: QOS out of actors
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

    def add_communicator(self, communicator: CommunicatorInterface):
        if communicator.name in self._communicators:
            raise ValueError(
                f"ERROR. Communicator with name [{communicator.name}] already present"
            )
        self._communicators[communicator.name] = communicator

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
            return sys._getframe(1).f_back.f_code.co_name
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
        self._logger.message_enter("++Proactor.process_message %s/%s", message.Header.Src, message.Header.MessageType)
        path_dbg = 0
        if not isinstance(message.Payload, MQTTReceiptPayload):
            path_dbg |= 0x00000001
            self._logger.message_summary(
                "IN  internal",
                self.name,
                f"{message.Header.Src}/{message.Header.MessageType}",
                message.Payload,
            )
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
            case _:
                path_dbg |= 0x00000040
                self._derived_process_message(message)
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
                            self.generate_event(PeerActiveEvent(PeerName=mqtt_receipt_message.Payload.client_name))
                            self._derived_recv_activated(transition)
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
                    case _:
                        path_dbg |= 0x00000100
                        self._derived_process_mqtt_message(mqtt_receipt_message, decoded_message)
                if decoded_message.Header.AckRequired:
                    path_dbg |= 0x00000200
                    if decoded_message.Header.MessageId:
                        path_dbg |= 0x00000400
                        self._publish_message(
                            mqtt_receipt_message.Payload.client_name,
                            Message(
                                Src=self.publication_name,
                                Payload=Ack(AckMessageID=decoded_message.Header.MessageId)
                            )
                        )
            case Err(error):
                path_dbg |= 0x00000800
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
                    for message_id in list(self._acks.keys()):
                        self._process_ack_result(message_id, AckWaitSummary.connection_failure)
            case Err(error):
                result = Err(error)
        return result

    def _process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]) -> Result[bool, BaseException]:
        return self._link_states.process_mqtt_connect_fail(message)

    def _upload_pending_events(self):
        ...

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
                    self.generate_event(PeerActiveEvent(PeerName=message.Payload.client_name))
                    result = self._derived_recv_activated(transition)
            case Err(error):
                path_dbg |= 0x00000010
                result = Err(error)
        self._logger.path(
            "--Proactor._process_mqtt_suback:%d  path:0x%08X",
            result.is_ok(),
            path_dbg,
        )
        return result

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

    def send(self, message: Message):
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

    def _send(self, message: Message):
        self.send(message)

    def generate_event(self, event: EventT) -> None:
        ...

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
