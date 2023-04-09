import logging
from abc import ABC, abstractmethod

from result import Ok
from result import Result

from actors.config import ScadaSettings
from gwproto.data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.driver_result import DriverResult


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
    def is_on(self) -> Result[DriverResult[int | None], Exception]:
        raise NotImplementedError

    def read_telemetry_value(self) -> Result[DriverResult[int | None], Exception]:
        return self.is_on()

    # noinspection PyMethodMayBeStatic
    def start(self) -> Result[DriverResult[bool], Exception]:
        return Ok(DriverResult(True))

