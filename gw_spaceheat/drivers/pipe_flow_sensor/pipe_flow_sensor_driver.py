from abc import ABC, abstractmethod
from typing import Optional
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent


class PipeFlowSensorDriver(ABC):
    def __init__(self, component: PipeFlowSensorComponent):
        if not isinstance(component, PipeFlowSensorComponent):
            raise Exception(
                f"PipeFlowSensorDriver requires PipeFlowSensorComponent. Got {component}"
            )
        self.component = component

    @abstractmethod
    def read_telemetry_value(self) -> Optional[int]:
        raise NotImplementedError
