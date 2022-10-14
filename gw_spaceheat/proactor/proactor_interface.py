"""Proactor interfaces, separate from implementations to clarify how users of this package interact with it and to
create forward references for implementation hiearchies
"""

import asyncio
from abc import ABC
from abc import abstractmethod

from proactor.message import Message


class CommunicatorInterface(ABC):
    """Pure interface necessary for interaction between a sub-object and the system services proactor"""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _send(self, message: Message):
        raise NotImplementedError

    @abstractmethod
    async def process_message(self, message: Message):
        raise NotImplementedError


class Communicator(CommunicatorInterface, ABC):
    """A partial implementation of CommunicatorInterface which supplies the trivial implementations"""

    _name: str
    _services: "ServicesInterface"

    def __init__(self, name: str, services: "ServicesInterface"):
        self._name = name
        self._services = services

    @property
    def name(self) -> str:
        return self._name

    def _send(self, message: Message):
        self._services.send(message)


class Runnable(ABC):
    """Pure interface to an object which is expected to support starting, stopping and joining."""

    @abstractmethod
    def start(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    @abstractmethod
    async def join(self):
        raise NotImplementedError

    async def stop_and_join(self):
        self.stop()
        await self.join()


class ServicesInterface(CommunicatorInterface):
    """Interface to system services (the proactor)"""

    @abstractmethod
    def get_communicator(self, name: str) -> CommunicatorInterface:
        raise NotImplementedError

    @abstractmethod
    def send(self, message: Message):
        raise NotImplementedError

    @abstractmethod
    def send_threadsafe(self, message: Message) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def async_receive_queue(self) -> asyncio.Queue:
        raise NotImplementedError
