from drivers.mcp23008 import mcp23008
import smbus

from drivers.boolean_actuator.boolean_actuator_base import BooleanActuator
from data_classes.actuator_component import ActuatorComponent

COMPONENT_ADDRESS = 0x20

class Ncd__Pr8_14_Spst__BooleanActuator(BooleanActuator):

    def __init__(self,  component: ActuatorComponent):
        super(Ncd__Pr8_14_Spst__BooleanActuator,self).__init__(component=component)
        bus = smbus.SMBus(1)
        gpio_output_map =  {0,1,2,3}
        kwargs = {'address': COMPONENT_ADDRESS, 'gpio_output_map': gpio_output_map}
        self.mcp23008_driver = mcp23008(bus, kwargs)

    def turn_on(self):
        self.mcp23008_driver.turn_on_relay(self.component.gpio)

    def turn_off(self):
        self.mcp23008_driver.turn_off_relay(self.component.gpio)


