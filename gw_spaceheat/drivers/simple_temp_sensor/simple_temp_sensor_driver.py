from abc import ABC, abstractmethod
import logging

from result import Ok
from result import Result

from gwproto.data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from actors.config import ScadaSettings
from drivers.driver_result import DriverResult


class SimpleTempSensorDriver(ABC):
    def __init__(self, component: SimpleTempSensorComponent, settings: ScadaSettings):
        if not isinstance(component, SimpleTempSensorComponent):
            raise Exception(f"TempSensorDriver requires TempSensorComponent. Got {component}")
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    # noinspection PyMethodMayBeStatic
    def start(self) -> Result[DriverResult[bool], Exception]:
        return Ok(DriverResult(True))

    @abstractmethod
    def read_telemetry_value(self) -> Result[DriverResult[int | None], Exception]:
        raise NotImplementedError
