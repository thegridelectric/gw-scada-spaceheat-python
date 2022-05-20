import pika
from drivers.boolean_actuator.boolean_actuator_base import BooleanActuator
from data_classes.actuator_component import ActuatorComponent



class Sim_Rabbit__BooleanActuator(BooleanActuator):

    def __init__(self,  component: ActuatorComponent):
        super(Sim_Rabbit__BooleanActuator,self).__init__(component=component)

    def turn_on(self):
        print(f"Need to send TURN ON rabbit msg to simulated element via gpio {self.component.gpio} ")

    def turn_off(self):
        print(f"Need to send TURN ON rabbit msg to simulated element via gpio {self.component.gpio} ")


