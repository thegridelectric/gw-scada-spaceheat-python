from abc import ABC, abstractmethod
import logging
from typing import Optional
from data_classes.components.temp_sensor_component import TempSensorComponent
from config import ScadaSettings


class TempSensorDriver(ABC):
    def __init__(self, component: TempSensorComponent, settings: ScadaSettings):
        if not isinstance(component, TempSensorComponent):
            raise Exception(f"TempSensorDriver requires TempSensorComponent. Got {component}")
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    @abstractmethod
    def read_telemetry_value(self) -> int:
        raise NotImplementedError
