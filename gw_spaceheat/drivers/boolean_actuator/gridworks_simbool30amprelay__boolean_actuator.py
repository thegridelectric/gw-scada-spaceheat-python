import pika
from drivers.boolean_actuator.boolean_actuator_base import BooleanActuator
from data_classes.boolean_actuator_component import BooleanActuatorComponent



class Gridworks__SimBool30AmpRelay__BooleanActuator(BooleanActuator):

    def __init__(self,  component: BooleanActuatorComponent):
        super(Gridworks__SimBool30AmpRelay__BooleanActuator,self).__init__(component=component)

    def turn_on(self):
        raise NotImplementedError(f"Need to send TURN ON rabbit msg to simulated element via gpio {self.component.gpio} ")

    def turn_off(self):
        raise NotImplementedError(f"Need to send TURN ON rabbit msg to simulated element via gpio {self.component.gpio} ")


