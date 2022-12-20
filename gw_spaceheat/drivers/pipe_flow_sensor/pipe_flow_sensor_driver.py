import logging
from abc import ABC, abstractmethod
from typing import Optional

from config import ScadaSettings
from data_classes.components.pipe_flow_sensor_component import \
    PipeFlowSensorComponent


class PipeFlowSensorDriver(ABC):
    def __init__(self, component: PipeFlowSensorComponent, settings: ScadaSettings):
        if not isinstance(component, PipeFlowSensorComponent):
            raise Exception(
                f"PipeFlowSensorDriver requires PipeFlowSensorComponent. Got {component}"
            )
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    @abstractmethod
    def read_telemetry_value(self) -> Optional[int]:
        raise NotImplementedError
