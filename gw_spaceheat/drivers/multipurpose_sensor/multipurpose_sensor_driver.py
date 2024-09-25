import logging
from abc import ABC, abstractmethod
from typing import Dict, List, NamedTuple, Optional

from actors.config import ScadaSettings
from gwproto.data_classes.components.ads111x_based_component import \
    Ads111xBasedComponent
from drivers.driver_result import DriverResult
from result import Ok, Result
from enums import TelemetryName


class TelemetrySpec(NamedTuple):
    AdsTerminalBlockIdx: int
    Type: TelemetryName


class MultipurposeSensorDriver(ABC):
    def __init__(self, component: Ads111xBasedComponent, settings: ScadaSettings):
        if not isinstance(component, Ads111xBasedComponent):
            raise Exception(
                f"MultipurposeSensorDriver requires Ads111xBasedComponent. Got {component}"
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
