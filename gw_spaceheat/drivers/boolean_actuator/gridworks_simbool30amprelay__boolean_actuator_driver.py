from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.boolean_actuator.boolean_actuator_driver import BooleanActuatorDriver
from schema.enums.make_model.make_model_map import MakeModel


class GridworksSimBool30AmpRelay_BooleanActuatorDriver(BooleanActuatorDriver):

    def __init__(self, component: BooleanActuatorComponent):
        super(GridworksSimBool30AmpRelay_BooleanActuatorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            raise Exception(f"Expected {MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY}, got {component.cac}")

    def turn_on(self):
        raise NotImplementedError(f"Need sim to turn on elt via gpio {self.component.gpio}")

    def turn_off(self):
        raise NotImplementedError(f"Need sim to turn on elt via gpio {self.component.gpio}")

    def is_on(self):
        return 0
