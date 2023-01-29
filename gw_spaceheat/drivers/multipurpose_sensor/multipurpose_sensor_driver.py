from abc import ABC, abstractmethod
import logging
from typing import Optional
from data_classes.components.multipurpose_sensor_component import MultipurposeSensorComponent
from actors2.config import ScadaSettings


class MultipurposeSensorDriver(ABC):
    def __init__(self, component: MultipurposeSensorComponent, settings: ScadaSettings):
        if not isinstance(component, MultipurposeSensorComponent):
            raise Exception(f"MultipurposeSensorDriver requires MultipurposeSensorComponent. Got {component}")
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    @abstractmethod
    def read_telemetry_values(self) -> List[int]:
        raise NotImplementedError
