"""Pure interface for a proactor sub-object (an Actor) which can communicate and has a GridWorks ShNode."""

import importlib
import sys
from abc import ABC, abstractmethod
from typing import Dict

from data_classes.sh_node import ShNode
from proactor.proactor_interface import CommunicatorInterface, Runnable, ServicesInterface


class ActorInterface(CommunicatorInterface, Runnable, ABC):

    @property
    @abstractmethod
    def alias(self) -> str:
        pass

    @property
    @abstractmethod
    def node(self) -> ShNode:
        pass

    @classmethod
    def load(cls, node: ShNode, services: ServicesInterface, module_name: str) -> "ActorInterface":
        if module_name not in sys.modules:
            importlib.import_module(module_name)
        actor_class = getattr(sys.modules[module_name], node.actor_class.value)
        return actor_class(node, services)

    @classmethod
    def load_all(cls, services: ServicesInterface, module_name: str) -> Dict[str, "ActorInterface"]:
        return {
            alias: cls.load(node, services, module_name=module_name)
            for alias, node in ShNode.by_alias.items()
        }