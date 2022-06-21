from abc import ABC, abstractmethod
from typing import Optional
from data_classes.components.temp_sensor_component import TempSensorComponent


class TempSensorDriver(ABC):
    def __init__(self, component: TempSensorComponent):
        if not isinstance(component, TempSensorComponent):
            raise Exception(f"TempSensorDriver requires TempSensorComponent. Got {component}")
        self.component = component

    @abstractmethod
    def read_telemetry_value(self) -> Optional[int]:
        raise NotImplementedError
