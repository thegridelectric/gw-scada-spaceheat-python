"""This packages provides infrastructure for running a proactor on top of asyncio with support multiple MQTT clients
and and sub-objects which support their own threads for synchronous operations.

This packages is not GridWorks-aware (except that it links actors with multiple mqtt clients). This separation between
communication / action infrastructure and GridWorks semantics is intended to allow the latter to be more focussed.

This package is not polished and the separation is up for debate.

Particular questions:
* Is the programming model still clean after more concrete actors are implemented and more infrastructure are added.
* Does the separation add value or just complicate analysis.
* MQTTClients should be made async.
* Semantics of building message type namespaces should be spelled out / further worked out.
* Test support should be implemented / cleaner.
"""

from proactor.message import Header, Message
from proactor.proactor_interface import (
    CommunicatorInterface,
    Communicator,
    Runnable,
    ServicesInterface,
)
from proactor.proactor_implementation import Proactor, MQTTCodec
from proactor.sync_thread import (
    AsyncQueueWriter,
    SyncAsyncQueueWriter,
    SyncAsyncInteractionThread,
)
from proactor.logger import ProactorLogger

__all__ = [
    "AsyncQueueWriter",
    "Communicator",
    "CommunicatorInterface",
    "Header",
    "Message",
    "MQTTCodec",
    "Proactor",
    "ProactorLogger",
    "Runnable",
    "ServicesInterface",
    "SyncAsyncInteractionThread",
    "SyncAsyncQueueWriter",
]
