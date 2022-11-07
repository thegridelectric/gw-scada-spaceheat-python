"""Proactor implementation"""

import asyncio
import enum
import functools
import traceback
from dataclasses import dataclass
from typing import Any
from typing import Awaitable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

import gwproto
from gwproto import MQTTCodec
from gwproto.messages import Ack
from gwproto.messages import EventT
from gwproto.messages import MQTTConnectEvent
from gwproto.messages import MQTTConnectFailedEvent
from gwproto.messages import MQTTDisconnectEvent
from gwproto.messages import MQTTFullySubscribedEvent
from gwproto.messages import ProblemEvent
from gwproto.messages import ShutdownEvent
from gwproto.messages import StartupEvent
from paho.mqtt.client import MQTTMessageInfo
from result import Err
from result import Ok
from result import Result

import config
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


@dataclass
class AckWaitInfo:
    message_id: str
    timer_handle: asyncio.TimerHandle
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


class Proactor(ServicesInterface, Runnable):
    _name: str
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _receive_queue: Optional[asyncio.Queue] = None
    _mqtt_clients: MQTTClients
    _mqtt_codecs: Dict[str, MQTTCodec]
    _communicators: Dict[str, CommunicatorInterface]
    _stop_requested: bool
    _tasks: List[asyncio.Task]
    _logger: ProactorLogger
    _acks: dict[str, AckWaitInfo]

    def __init__(self, name: str, logger: ProactorLogger):
        self._name = name
        self._logger = logger
        self._mqtt_clients = MQTTClients()
        self._mqtt_codecs = dict()
        self._communicators = dict()
        self._tasks = []
        self._acks = dict()
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

    def _start_ack_timer(self, message_id: str, context: Any = None, delay: Optional[float] = None) -> None:
        if delay is None:
            delay = 5
        self._acks[message_id] = AckWaitInfo(
            message_id,
            asyncio.get_running_loop().call_later(
                delay,
                functools.partial(self._process_ack_timeout, message_id),
            ),
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
        self._logger.path("++Proactor._process_ack_timeout %s", message_id)
        self._process_ack_result(message_id, AckWaitSummary.timeout)
        self._logger.path("--Proactor._process_ack_timeout")

    def _derived_process_ack_result(self, result: AckWaitResult):
        ...

    def _process_ack_result(self, message_id: str, reason: AckWaitSummary):
        self._logger.path("++Proactor._process_ack_result %s", message_id)
        path_dbg = 0
        wait_info = self._cancel_ack_timer(message_id)
        if wait_info is not None:
            path_dbg |= 0x00000001
            self._derived_process_ack_result(AckWaitResult(summary=reason, wait_info=wait_info))
        self._logger.path("--Proactor._process_ack_result path:0x%08X", path_dbg)

    # TODO: QOS out of actors
    def _publish_message(self, client, message: Message, qos: int = 0, context: Any = None) -> MQTTMessageInfo:
        topic = message.mqtt_topic()
        payload = self._mqtt_codecs[client].encode(message)
        self._logger.message_summary("OUT mqtt    ", message.Header.Src, topic, message.Payload)
        if message.Header.AckRequired:
            self._start_ack_timer(message.Header.MessageId, context)
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
            while not self._stop_requested:
                message = await self._receive_queue.get()
                if not self._stop_requested:
                    await self.process_message(message)
                self._receive_queue.task_done()
        # TODO: Clean this up
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
            asyncio.create_task(self.process_messages(), name="process_messages")
        ]
        self._start_derived_tasks()

    def _start_derived_tasks(self):
        pass

    def _derived_process_message(self, message: Message):
        pass

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        pass

    async def process_message(self, message: Message):
        self._logger.path("++Proactor.process_message %s/%s", message.Header.Src, message.Header.MessageType)
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
        self._logger.path("--Proactor.process_message  path:0x%08X", path_dbg)

    def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        self._logger.path("++Proactor._process_mqtt_message %s/%s", message.Header.Src, message.Header.MessageType)
        path_dbg = 0
        decoder = self._mqtt_codecs.get(message.Payload.client_name, None)
        result: Result[Message[Any], Exception]
        try:
            result = Ok(decoder.decode(message.Payload.message.topic, message.Payload.message.payload))
        except Exception as e:
            path_dbg |= 0x00000001
            self._logger.exception("ERROR decoding [%s]", message.Payload)
            self.generate_event(
                ProblemEvent(
                    ProblemType=gwproto.messages.Problems.warning,
                    Summary=f"Decoding error topic [{message.Payload.message.topic}]  error [{type(e)}]",
                    Details=(
                        f"Topic: {message.Payload.message.topic}\n"
                        f"Message: {message.Payload.message.payload[:70]}"
                        f"{'...' if len(message.Payload.message.payload)> 70 else ''}\n"
                        f"{traceback.format_exception(e)}\n"
                        f"Exception: {e}"
                    )
                )
            )
            result = Err(e)
        if result:
            path_dbg |= 0x00000002
            self._logger.message_summary("IN  mqtt    ", self.name, message.Payload.message.topic, result.value.Payload)
            match result.value.Payload:
                case Ack():
                    self._process_ack_result(result.value.Payload.AckMessageID, AckWaitSummary.acked)
                case _:
                    path_dbg |= 0x00000008
                    self._derived_process_mqtt_message(message, result.value)
        if result.is_ok() and result.value.Header.AckRequired:
            path_dbg |= 0x00000010
            if result.value.Header.MessageId:
                path_dbg |= 0x00000020
                self._publish_message(
                    message.Payload.client_name,
                    Message(
                        Src=self.publication_name,
                        Payload=Ack(AckMessageID=result.value.Header.MessageId)
                    )
                )
        self._logger.path("--Proactor._process_mqtt_message:%s  path:0x%08X", int(result.is_ok()), path_dbg)

    def _process_mqtt_connected(self, message: Message[MQTTConnectPayload]):
        self._mqtt_clients.subscribe_all(message.Payload.client_name)
        self.generate_event(MQTTConnectEvent())

    def _process_mqtt_disconnected(self, message: Message[MQTTDisconnectPayload]):
        for message_id in list(self._acks.keys()):
            self._process_ack_result(message_id, AckWaitSummary.connection_failure)
        self.generate_event(MQTTDisconnectEvent())

    def _process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]):
        self.generate_event(MQTTConnectFailedEvent())

    def _process_mqtt_suback(self, message: Message[MQTTSubackPayload]):
        if message.Payload.num_pending_subscriptions == 0:
            self.generate_event(MQTTFullySubscribedEvent())

    async def run_forever(self):
        self._loop = asyncio.get_running_loop()
        self._receive_queue = asyncio.Queue()
        self._mqtt_clients.start(self._loop, self._receive_queue)
        for communicator in self._communicators.values():
            if isinstance(communicator, Runnable):
                communicator.start()
        self.start_tasks()
        self.generate_event(StartupEvent())
        await self.join()

    def stop_mqtt(self):
        self._mqtt_clients.stop()

    def start(self):
        # TODO clean up this interface for proactor
        raise RuntimeError("ERROR. Proactor must be started by awaiting run_forever()")

    def stop(self):
        self._stop_requested = True
        for task in self._tasks:
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
