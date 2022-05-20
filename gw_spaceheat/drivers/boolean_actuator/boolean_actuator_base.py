from abc import ABC, abstractmethod
from data_classes.actuator_component import ActuatorComponent
class BooleanActuator(ABC):

    def __init__(self, component: ActuatorComponent):
        self.component = component

    @abstractmethod
    def turn_on(self):
        raise NotImplementedError

    @abstractmethod
    def turn_off(self):
        raise NotImplementedError