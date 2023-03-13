from result import Ok
from result import Result

from actors.config import ScadaSettings
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from drivers.driver_result import DriverResult
from enums import MakeModel


class UnknownBooleanActuatorDriver(BooleanActuatorDriver):
    state: int

    def __init__(self, component: BooleanActuatorComponent, settings: ScadaSettings):
        super(UnknownBooleanActuatorDriver, self).__init__(component=component, settings=settings)
        if component.cac.make_model != MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            raise Exception(f"Expected {MakeModel.UNKNOWNMAKE__UNKNOWNMODEL}, got {component.cac}")
        self.state = 0

    def turn_on(self):
        self.state = 1

    def turn_off(self):
        self.state = 0

    def is_on(self) -> Result[DriverResult[int | None], Exception]:
        return Ok(DriverResult(self.state))
