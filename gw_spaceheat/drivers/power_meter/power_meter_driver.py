import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from actors2.config import ScadaSettings
from data_classes.components.electric_meter_component import \
    ElectricMeterComponent
from schema.enums import TelemetryName


class PowerMeterDriver(ABC):
    def __init__(self, component: ElectricMeterComponent, settings: ScadaSettings):
        if not isinstance(component, ElectricMeterComponent):
            raise Exception(f"ElectricMeterDriver requires ElectricMeterComponent. Got {component}")
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    def start(self):
        pass

    @abstractmethod
    def read_current_rms_micro_amps(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def read_hw_uid(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def read_power_w(self) -> Optional[int]:
        raise NotImplementedError

    def telemetry_name_list(self) -> List[TelemetryName]:
        return self.component.cac.telemetry_name_list()

    def read_telemetry_value(self, telemetry_name: TelemetryName) -> int:
        if telemetry_name not in self.telemetry_name_list():
            raise Exception(f"driver for {self.component.cac} does not read {telemetry_name}")
        if telemetry_name == TelemetryName.CURRENT_RMS_MICRO_AMPS:
            return self.read_current_rms_micro_amps()
        elif telemetry_name == TelemetryName.POWER_W:
            return self.read_power_w()
        else:
            raise Exception(f"Driver {self} not set up to read {telemetry_name}")
