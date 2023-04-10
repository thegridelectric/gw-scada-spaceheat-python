import logging
from abc import ABC, abstractmethod

from actors.config import ScadaSettings
from drivers.driver_result import DriverResult
from gwproto.data_classes.components.relay_component import RelayComponent
from result import Ok, Result


class RelayDriver(ABC):
    def __init__(self, component: RelayComponent, settings: ScadaSettings):
        if not isinstance(component, RelayComponent):
            raise Exception(f"RelayDriver requires RelayComponent. Got {component}")
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
