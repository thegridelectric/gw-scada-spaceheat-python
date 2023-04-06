"""GridWorks Scada functionality beyond proactor.ServicesInterface"""

from abc import ABC
from abc import abstractmethod

from result import Result

from actors.actor_interface import ActorInterface
from actors.config import ScadaSettings
from actors.scada_data import ScadaData
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproactor.proactor_interface import ServicesInterface


class ScadaInterface(ServicesInterface, ActorInterface, ABC):

    @property
    @abstractmethod
    def hardware_layout(self) -> HardwareLayout:
        ...

    @property
    @abstractmethod
    def settings(self) -> ScadaSettings:
        ...

    @property
    @abstractmethod
    def data(self) -> ScadaData:
        ...
