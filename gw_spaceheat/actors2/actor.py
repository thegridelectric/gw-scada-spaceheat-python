"""A partial implementation of ActorInterface which supplies the trivial implementations"""

from abc import ABC

from actors2.actor_interface import ActorInterface
from actors2.scada_interface import ScadaInterface
from data_classes.sh_node import ShNode
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
