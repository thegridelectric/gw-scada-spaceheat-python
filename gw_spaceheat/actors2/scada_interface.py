"""GridWorks Scada functionality beyond proactor.ServicesInterface"""

from abc import ABC
from abc import abstractmethod

from actors2.actor_interface import ActorInterface
from actors2.config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from proactor.proactor_interface import ServicesInterface


class ScadaInterface(ServicesInterface, ActorInterface, ABC):
    @property
    @abstractmethod
    def settings(self) -> ScadaSettings:
        pass

    @property
    @abstractmethod
    def hardware_layout(self) -> HardwareLayout:
        pass
