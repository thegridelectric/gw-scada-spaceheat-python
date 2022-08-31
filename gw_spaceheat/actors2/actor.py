"""Actor: A partial implementation of ActorInterface which supplies the trivial implementations.

SyncThreadActor: An actor which orchestrates starting, stopping and communicating with a passed in
SyncAsyncInteractionThread
"""


from abc import ABC
from typing import TypeVar, Generic, Any

from actors2.actor_interface import ActorInterface
from actors2.scada_interface import ScadaInterface
from data_classes.sh_node import ShNode
from proactor import SyncAsyncInteractionThread, Message
from proactor.proactor_interface import Communicator


class Actor(ActorInterface, Communicator, ABC):

    _node: ShNode

    def __init__(self, node: ShNode, services: ScadaInterface):
        self._node = node
        super().__init__(node.alias, services)

    @property
    def services(self):
        return self._services

    @property
    def alias(self):
        return self._name

    @property
    def node(self):
        return self._node


SyncThreadT = TypeVar("SyncThreadT", bound=SyncAsyncInteractionThread)


class SyncThreadActor(Actor, Generic[SyncThreadT]):
    _sync_thread: SyncAsyncInteractionThread

    def __init__(
        self,
        node: ShNode,
        services: ScadaInterface,
        sync_thread: SyncAsyncInteractionThread,
    ):
        super().__init__(node, services)
        self._sync_thread = sync_thread

    async def process_message(self, message: Message):
        raise ValueError(f"Error. {self.__class__.__name__} does not process any messages. Received {message.header}")

    def send_driver_message(self, message: Any) -> None:
        self._sync_thread.put_to_sync_queue(message)

    def start(self):
        self._sync_thread.start()

    def stop(self):
        self._sync_thread.request_stop()

    async def join(self):
        await self._sync_thread.async_join()
