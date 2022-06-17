from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.boolean_actuator.boolean_actuator_driver import BooleanActuatorDriver
from schema.enums.make_model.make_model_map import MakeModel
import time


class GridworksSimBool30AmpRelay_BooleanActuatorDriver(BooleanActuatorDriver):

    def __init__(self, component: BooleanActuatorComponent):
        super(GridworksSimBool30AmpRelay_BooleanActuatorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            raise Exception(f"Expected {MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY}, got {component.cac}")
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

    def is_on(self) -> int:
        self.cmd_delay()
        return self._fake_relay_state
