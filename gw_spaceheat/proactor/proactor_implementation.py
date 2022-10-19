"""Proactor implementation"""

import asyncio
import traceback
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Awaitable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

from paho.mqtt.client import MQTTMessageInfo

import config
from proactor.logger import ProactorLogger
from proactor.message import Message
from proactor.message import MessageType
from proactor.message import MQTTConnectFailPayload
from proactor.message import MQTTConnectPayload
from proactor.message import MQTTDisconnectPayload
from proactor.message import MQTTReceiptPayload
from proactor.message import MQTTSubackPayload
from proactor.mqtt import MQTTClients
from proactor.proactor_interface import CommunicatorInterface
from proactor.proactor_interface import Runnable
from proactor.proactor_interface import ServicesInterface
from proactor.sync_thread import AsyncQueueWriter


class MQTTCodec(ABC):
    @abstractmethod
    def encode(self, content: Any) -> bytes:
        pass

    @abstractmethod
    def decode(self, receipt_payload: MQTTReceiptPayload) -> Any:
        pass


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

    # TODO: Clean up loop control
    def __init__(self, name: str, logger: ProactorLogger):
        self._name = name
        self._logger = logger
        # TODO: Figure out and remove the deprecation warning this produces.
        self._mqtt_clients = MQTTClients(AsyncQueueWriter())
        self._mqtt_codecs = dict()
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

    def _encode_and_publish(
        self, client: str, topic: str, payload: Any, qos: int
    ) -> MQTTMessageInfo:
        self._logger.message_summary("OUTq", client, topic, payload)
        encoder = self._mqtt_codecs[client]
        return self._mqtt_clients.publish(client, topic, encoder.encode(payload), qos)

    # TODO: QOS out of actors
    def _publish_message(self, client, message: Message, qos: int = 0) -> MQTTMessageInfo:
        topic = message.mqtt_topic()
        self._logger.message_summary("OUTq", client, topic, message)
        return self._mqtt_clients.publish(client, topic, self._mqtt_codecs[client].encode(message), qos)

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
                self._logger.error("Stopping procator")
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

    async def _derived_process_message(self, message: Message):
        pass

    async def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        pass

    async def process_message(self, message: Message):
        self._logger.path("++Proactor.process_message %s/%s", message.header.src, message.header.message_type)
        path_dbg = 0
        self._logger.message_summary(
            "INx ",
            self.name,
            f"{message.header.src}/{message.header.message_type}",
            message.payload,
        )
        # TODO: be easier on the eyes
        if message.header.message_type == MessageType.mqtt_message.value:
            path_dbg |= 0x00000001
            await self._process_mqtt_message(message)
        elif message.header.message_type == MessageType.mqtt_connected.value:
            path_dbg |= 0x00000002
            self._process_mqtt_connected(message)
        elif message.header.message_type == MessageType.mqtt_disconnected.value:
            path_dbg |= 0x00000004
            self._process_mqtt_disconnected(message)
        elif message.header.message_type == MessageType.mqtt_connect_failed.value:
            path_dbg |= 0x00000008
            self._process_mqtt_connect_fail(message)
        elif message.header.message_type == MessageType.mqtt_suback.value:
            self._process_mqtt_suback(message)
        else:
            path_dbg |= 0x00000010
            await self._derived_process_message(message)
        self._logger.path("--Proactor.process_message  path:0x%08X", path_dbg)

    async def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        self._logger.path("++Proactor._process_mqtt_message %s/%s", message.header.src, message.header.message_type)
        path_dbg = 0
        decoder = self._mqtt_codecs.get(message.payload.client_name, None)
        if decoder is not None:
            path_dbg |= 0x00000001
            decoded = decoder.decode(message.payload)
        else:
            path_dbg |= 0x00000002
            decoded = message.payload
        self._logger.message_summary("INq ", self.name, message.payload.message.topic, decoded)
        await self._derived_process_mqtt_message(message, decoded)
        self._logger.path("--Proactor._process_mqtt_message  path:0x%08X", path_dbg)

    def _process_mqtt_connected(self, message: Message[MQTTConnectPayload]):
        self._mqtt_clients.subscribe_all(message.payload.client_name)

    def _process_mqtt_disconnected(self, message: Message[MQTTDisconnectPayload]):
        pass

    def _process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]):
        pass

    def _process_mqtt_suback(self, message: Message[MQTTSubackPayload]):
        pass

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
            "OUTx",
            message.header.src,
            f"{message.header.dst}/{message.header.message_type}",
            message.payload,
        )
        self._receive_queue.put_nowait(message)

    def send_threadsafe(self, message: Message) -> None:
        self._loop.call_soon_threadsafe(self._receive_queue.put_nowait, message)

    def get_communicator(self, name: str) -> CommunicatorInterface:
        return self._communicators[name]

    @property
    def name(self) -> str:
        return self._name

    def _send(self, message: Message):
        self.send(message)


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
