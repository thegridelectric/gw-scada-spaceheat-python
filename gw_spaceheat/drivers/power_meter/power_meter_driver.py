import logging
from abc import ABC, abstractmethod

from result import Err
from result import Ok
from result import Result

from actors.config import ScadaSettings
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.components.electric_meter_component import \
    ElectricMeterComponent
from drivers.driver_result import DriverResult
from enums import TelemetryName


class PowerMeterDriver(ABC):
    component: ElectricMeterComponent
    settings: ScadaSettings
    logger: logging.Logger

    def __init__(self, component: ElectricMeterComponent, settings: ScadaSettings):
        if not isinstance(component, ElectricMeterComponent):
            raise Exception(f"ElectricMeterDriver requires ElectricMeterComponent. Got {component}")
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    def start(self) -> Result[DriverResult, Exception]:
        return Ok(DriverResult(True))

    @abstractmethod
    def read_hw_uid(self) -> Result[DriverResult[str | None], Exception]:
        raise NotImplementedError

    @abstractmethod
    def read_current_rms_micro_amps(self, node: ShNode) -> Result[DriverResult[int | None], Exception]:
        raise NotImplementedError

    @abstractmethod
    def read_power_w(self, node: ShNode) -> Result[DriverResult[int | None], Exception]:
        raise NotImplementedError

    def read_telemetry_value(self,
                             node: ShNode,
                             telemetry_name: TelemetryName) -> Result[DriverResult[int | None], Exception]:
        if telemetry_name == TelemetryName.PowerW:
            return self.read_power_w(node)
        elif telemetry_name == TelemetryName.CurrentRmsMicroAmps:
            return self.read_current_rms_micro_amps(node)
        elif  telemetry_name not in self.component.cac.TelemetryNameList:
            raise Exception(f"driver for {self.component.cac} does not read {telemetry_name}")
        else:
            return Err(ValueError(f"Driver {self} not set up to read {telemetry_name}"))
