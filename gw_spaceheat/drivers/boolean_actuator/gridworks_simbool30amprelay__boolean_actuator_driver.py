from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.boolean_actuator.boolean_actuator_driver import BooleanActuatorDriver


class GridworksSimBool30AmpRelay_BooleanActuatorDriver(BooleanActuatorDriver):

    def __init__(self, component: BooleanActuatorComponent):
        super(GridworksSimBool30AmpRelay_BooleanActuatorDriver, self).__init__(component=component)

    def turn_on(self):
        raise NotImplementedError(f"Need sim to turn on elt via gpio {self.component.gpio}")

    def turn_off(self):
        raise NotImplementedError(f"Need sim to turn on elt via gpio {self.component.gpio}")


