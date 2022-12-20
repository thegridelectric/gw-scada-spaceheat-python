import logging
from abc import ABC, abstractmethod

from actors2.config import ScadaSettings
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent


class BooleanActuatorDriver(ABC):
    def __init__(self, component: BooleanActuatorComponent, settings: ScadaSettings):
        if not isinstance(component, BooleanActuatorComponent):
            raise Exception(
                f"BooleanActuatorDriver requires BooleanActuatorComponent. Got {component}"
            )
        self.component = component
        self.settings: ScadaSettings = settings
        self.logger = logging.getLogger(settings.logging.base_log_name)

    @abstractmethod
    def turn_on(self):
        raise NotImplementedError

    @abstractmethod
    def turn_off(self):
        raise NotImplementedError

    @abstractmethod
    def is_on(self) -> int:
        raise NotImplementedError
