from abc import ABC, abstractmethod
from typing import Optional
from data_classes.components.electric_meter_component import ElectricMeterComponent


class PowerMeterDriver(ABC):
    def __init__(self, component: ElectricMeterComponent):
        if not isinstance(component, ElectricMeterComponent):
            raise Exception(f"ElectricMeterDriver requires ElectricMeterComponent. Got {component}")
        self.component = component

    @abstractmethod
    def read_current_rms_micro_amps(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def read_hw_uid(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def read_power_w(self) -> Optional[int]:
        raise NotImplementedError
