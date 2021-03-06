from abc import ABC, abstractmethod

from data_classes.components.boolean_actuator_component import BooleanActuatorComponent


class BooleanActuatorDriver(ABC):
    def __init__(self, component: BooleanActuatorComponent):
        if not isinstance(component, BooleanActuatorComponent):
            raise Exception(
                f"BooleanActuatorDriver requires BooleanActuatorComponent. Got {component}"
            )
        self.component = component

    @abstractmethod
    def turn_on(self):
        raise NotImplementedError

    @abstractmethod
    def turn_off(self):
        raise NotImplementedError

    @abstractmethod
    def is_on(self) -> int:
        raise NotImplementedError
