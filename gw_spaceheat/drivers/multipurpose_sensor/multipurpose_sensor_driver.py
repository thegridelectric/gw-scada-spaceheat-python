import logging
from abc import ABC, abstractmethod
from typing import Dict, List, NamedTuple, Optional

from actors.config import ScadaSettings
from data_classes.components.multipurpose_sensor_component import \
    MultipurposeSensorComponent
from drivers.driver_result import DriverResult
from result import Ok, Result
from schema.enums import TelemetryName


class TelemetrySpec(NamedTuple):
    ChannelIdx: int
    Type: TelemetryName


class MultipurposeSensorDriver(ABC):
    def __init__(self, component: MultipurposeSensorComponent, settings: ScadaSettings):
        if not isinstance(component, MultipurposeSensorComponent):
            raise Exception(
                f"MultipurposeSensorDriver requires MultipurposeSensorComponent. Got {component}"
            )
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    def start(self) -> Result[DriverResult, Exception]:
        return Ok(DriverResult(True))

    @abstractmethod
    def read_telemetry_values(
        self, channel_telemetry_list: List[TelemetrySpec]
    ) -> Result[DriverResult[Dict[TelemetrySpec, int]], Exception]:
        raise NotImplementedError
