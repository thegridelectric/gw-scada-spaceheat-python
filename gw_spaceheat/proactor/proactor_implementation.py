"""Proactor implementation"""

import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import Dict, List, Awaitable, Any, Optional

from paho.mqtt.client import MQTTMessageInfo

import config
from actors.utils import MessageSummary
from proactor.message import (
    Message,
    KnownNames,
    MessageType,
    MQTTConnectPayload,
    MQTTReceiptPayload,
    MQTTConnectFailPayload,
    MQTTDisconnectPayload,
    MQTTSubackPayload,
)
from proactor.mqtt import MQTTClients
from proactor.proactor_interface import (
    ServicesInterface,
    Runnable,
    CommunicatorInterface,
)
from proactor.sync_thread import AsyncQueueWriter


def _print_tasks(loop_, tag="", tasks=None):
    # TODO: Move this to some general debugging location
    if tasks is None:
        tasks = asyncio.all_tasks(loop_)
    print(f"Tasks: {len(tasks)}  [{tag}]")

    def _exception(task_):
        try:
            exception_ = task_.exception()
        except asyncio.CancelledError as e:
            exception_ = e
        except asyncio.InvalidStateError:
            exception_ = None
        return exception_

    for i, task in enumerate(tasks):
        print(
            f"\t{i+1}/{len(tasks)}  {task.get_name():20s}  done:{task.done()}   exception:{_exception(task)}  {task.get_coro()}"
        )


class MQTTCodec(ABC):
    @abstractmethod
    def encode(self, payload: Any) -> bytes:
        pass

    @abstractmethod
    def decode(self, receipt_payload: MQTTReceiptPayload) -> Any:
        pass


class Proactor(ServicesInterface, Runnable):
    _name: str
    _loop: asyncio.AbstractEventLoop
    _receive_queue: asyncio.Queue
    _mqtt_clients: MQTTClients
    _mqtt_codecs: Dict[str, MQTTCodec]
    _communicators: Dict[str, CommunicatorInterface]
    _stop_requested: bool
    _tasks: List[asyncio.Task]

    # TODO: Clean up loop control
    def __init__(self, name: str = KnownNames.proactor.value):
        self._name = name
        # TODO: Figure out and remove the deprecation warning this produces.
        self._loop = asyncio.get_event_loop()
        self._receive_queue = asyncio.Queue()
        self._mqtt_clients = MQTTClients(
            AsyncQueueWriter(self._loop, self._receive_queue)
        )
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
        print(MessageSummary.format("OUTq", client, topic, payload))
        encoder = self._mqtt_codecs[client]
        return self._mqtt_clients.publish(client, topic, encoder.encode(payload), qos)

    def add_communicator(self, communicator: CommunicatorInterface):
        if communicator.name in self._communicators:
            raise ValueError(
                f"ERROR. Communicator with name [{communicator.name}] already present"
            )
        self._communicators[communicator.name] = communicator

    @property
    def async_receive_queue(self):
        return self._receive_queue

    async def process_messages(self):
        try:
            while not self._stop_requested:
                message = await self._receive_queue.get()
                if not self._stop_requested:
                    await self.process_message(message)
                self._receive_queue.task_done()
        # TODO: Clean this up
        except Exception as e:
            print(f"ERROR in process_message: {e}")
            traceback.print_exc()
            print("Stopping procator")
            self.stop()

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
        print(
            f"++Proactor.process_message {message.header.src}/{message.header.message_type}"
        )
        path_dbg = 0
        print(
            MessageSummary.format(
                "INx ",
                self.name,
                f"{message.header.src}/{message.header.message_type}",
                message.payload,
            )
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
        print(f"--Proactor.process_message  path:0x{path_dbg:08X}")

    async def _process_mqtt_message(self, message: Message[MQTTReceiptPayload]):
        print(
            f"++Proactor._process_mqtt_message {message.header.src}/{message.header.message_type}"
        )
        path_dbg = 0
        decoder = self._mqtt_codecs.get(message.payload.client_name, None)
        if decoder is not None:
            path_dbg |= 0x00000001
            decoded = decoder.decode(message.payload)
        else:
            path_dbg |= 0x00000002
            decoded = message.payload
        print(
            MessageSummary.format(
                "INq ", self.name, message.payload.message.topic, decoded
            )
        )
        await self._derived_process_mqtt_message(message, decoded)
        print(f"--Proactor._process_mqtt_message  path:0x{path_dbg:08X}")

    def _process_mqtt_connected(self, message: Message[MQTTConnectPayload]):
        self._mqtt_clients.subscribe_all(message.payload.client_name)

    def _process_mqtt_disconnected(self, message: Message[MQTTDisconnectPayload]):
        pass

    def _process_mqtt_connect_fail(self, message: Message[MQTTConnectFailPayload]):
        pass

    def _process_mqtt_suback(self, message: Message[MQTTSubackPayload]):
        pass

    async def run_forever(self):
        self.start_tasks()
        await self.join()

    def start_mqtt(self):
        self._mqtt_clients.start()

    def stop_mqtt(self):
        self._mqtt_clients.stop()

    def start(self):
        self.start_mqtt()
        for communicator in self._communicators.values():
            if isinstance(communicator, Runnable):
                communicator.start()

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
        print("++Proactor.join()")
        _print_tasks(self._loop, "Proactor.join() - all tasks")
        running: List[Awaitable] = self._tasks[:]
        for communicator in self._communicators.values():
            communicator_name = communicator.name
            if isinstance(communicator, Runnable):
                running.append(
                    self._loop.create_task(
                        communicator.join(), name=f"{communicator_name}.join"
                    )
                )
        try:
            while running:
                _print_tasks(self._loop, "WAITING FOR", tasks=running)
                done, running = await asyncio.wait(running, return_when="FIRST_COMPLETED")
                _print_tasks(self._loop, tag="DONE", tasks=done)
                _print_tasks(self._loop, tag="PENDING", tasks=running)
                for task in done:
                    print("")
                    if exception := task.exception():
                        print(f"EXCEPTION in task {task.get_name()}  {exception}")
                        traceback.print_tb(exception.__traceback__)
        except Exception as e:
            print(f"ERROR in Proactor.join: {e}")
            traceback.print_tb(e.__traceback__)
        print("--Proactor.join()")

    def publish(self, client: str, topic: str, payload: bytes, qos: int):
        self._mqtt_clients.publish(client, topic, payload, qos)

    def send(self, message: Message):
        print(
            MessageSummary.format(
                "OUTx",
                message.header.src,
                f"{message.header.dst}/{message.header.message_type}",
                message.payload,
            )
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
