from abc import ABC, abstractmethod
import logging
from typing import Optional
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from actors2.config import ScadaSettings


class SimpleTempSensorDriver(ABC):
    def __init__(self, component: SimpleTempSensorComponent, settings: ScadaSettings):
        if not isinstance(component, SimpleTempSensorComponent):
            raise Exception(f"TempSensorDriver requires TempSensorComponent. Got {component}")
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    @abstractmethod
    def read_telemetry_value(self) -> int:
        raise NotImplementedError
