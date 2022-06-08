from abc import ABC, abstractmethod

from data_classes.component import Component
from data_classes.cacs.temp_sensor_cac import TempSensorCac


class TempSensorDriver(ABC):
    def __init__(self, component: Component):
        if not isinstance(component.cac, TempSensorCac):
            raise Exception(f"component {component} is not a TempSensor!!")
        self.component = component

    @abstractmethod
    def read_temp(self):
        raise NotImplementedError
