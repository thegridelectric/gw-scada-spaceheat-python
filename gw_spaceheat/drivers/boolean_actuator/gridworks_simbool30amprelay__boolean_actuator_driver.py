import time

from result import Ok
from result import Result

from actors.config import ScadaSettings
from gwproto.data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from drivers.driver_result import DriverResult
from enums import MakeModel


class GridworksSimBool30AmpRelay_BooleanActuatorDriver(BooleanActuatorDriver):
    def __init__(self, component: BooleanActuatorComponent, settings: ScadaSettings):
        super(GridworksSimBool30AmpRelay_BooleanActuatorDriver, self).__init__(component=component, settings=settings)
        if component.cac.make_model != MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            raise Exception(
                f"Expected {MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY}, got {component.cac}"
            )
        self.component = component
        self._fake_relay_state = 0

    def cmd_delay(self):
        delay_s = self.component.cac.typical_response_time_ms / 1000
        time.sleep(delay_s)

    def turn_on(self):
        self.cmd_delay()
        self._fake_relay_state = 1

    def turn_off(self):
        self.cmd_delay()
        self._fake_relay_state = 0

    def is_on(self) -> Result[DriverResult[int | None], Exception]:
        self.cmd_delay()
        return Ok(DriverResult(self._fake_relay_state))
