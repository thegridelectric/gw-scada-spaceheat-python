"""GridWorks Scada functionality beyond proactor.ServicesInterface"""

from abc import ABC, abstractmethod

from config import ScadaSettings
from actors2.actor_interface import ActorInterface
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
