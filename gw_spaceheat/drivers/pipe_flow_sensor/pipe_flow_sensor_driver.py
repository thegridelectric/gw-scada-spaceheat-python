import logging
from abc import ABC, abstractmethod

from result import Ok
from result import Result

from actors2.config import ScadaSettings
from data_classes.components.pipe_flow_sensor_component import \
    PipeFlowSensorComponent
from drivers.driver_result import DriverResult


class PipeFlowSensorDriver(ABC):
    def __init__(self, component: PipeFlowSensorComponent, settings: ScadaSettings):
        if not isinstance(component, PipeFlowSensorComponent):
            raise Exception(
                f"PipeFlowSensorDriver requires PipeFlowSensorComponent. Got {component}"
            )
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    # noinspection PyMethodMayBeStatic
    def start(self) -> Result[DriverResult[bool], Exception]:
        return Ok(DriverResult(True))


    @abstractmethod
    def read_telemetry_value(self) -> Result[DriverResult[int | None], Exception]:
        raise NotImplementedError
