from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from drivers.boolean_actuator.boolean_actuator_driver import BooleanActuatorDriver
from schema.enums import MakeModel


class UnknownBooleanActuatorDriver(BooleanActuatorDriver):
    def __init__(self, component: BooleanActuatorComponent):
        super(UnknownBooleanActuatorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            raise Exception(f"Expected {MakeModel.UNKNOWNMAKE__UNKNOWNMODEL}, got {component.cac}")

    def turn_on(self):
        raise NotImplementedError("UnknownBooleanActuatorDriver!")

    def turn_off(self):
        raise NotImplementedError("UnknownBooleanActuatorDriver!")

    def is_on(self):
        raise NotImplementedError("UnknownBooleanActuatorDriver!")
