import logging
from abc import ABC, abstractmethod
from typing import Dict, List

from actors.config import ScadaSettings
from gwproto.data_classes.components.ads111x_based_component import \
    Ads111xBasedComponent
from gwproto.data_classes.data_channel import DataChannel
from drivers.driver_result import DriverOutcome
from result import Ok, Result




class MultipurposeSensorDriver(ABC):
    def __init__(self, component: Ads111xBasedComponent, settings: ScadaSettings):
        if not isinstance(component, Ads111xBasedComponent):
            raise Exception(
                f"MultipurposeSensorDriver requires Ads111xBasedComponent. Got {component}"
            )
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    def start(self) -> Result[DriverOutcome[bool], Exception]:
        return Ok(DriverOutcome(True))

    @abstractmethod
    def read_telemetry_values(
        self, data_channels: List[DataChannel]
    ) -> Result[DriverOutcome[Dict[str, int]], Exception]: # names of DataChannels
        raise NotImplementedError
