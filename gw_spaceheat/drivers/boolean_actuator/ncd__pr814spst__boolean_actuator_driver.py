from enum import Enum

import schema.property_format as property_format
import smbus2 as smbus
from config import ScadaSettings
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.base.mcp23008 import mcp23008
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from schema.enums import MakeModel

COMPONENT_I2C_ADDRESS = 0x20


class I2CErrorEnum(Enum):
    NO_ADDRESS_ERROR = -100000
    READ_ERROR = -200000


class NcdPr814Spst_BooleanActuatorDriver(BooleanActuatorDriver):
    def __init__(self, component: BooleanActuatorComponent, settings: ScadaSettings):
        super(NcdPr814Spst_BooleanActuatorDriver, self).__init__(component=component, settings=settings)
        if component.cac.make_model != MakeModel.NCD__PR814SPST:
            raise Exception(f"Expected {MakeModel.NCD__PR814SPST}, got {component.cac}")
        bus = smbus.SMBus(1)
        gpio_output_map = {0, 1, 2, 3}
        kwargs = {"address": COMPONENT_I2C_ADDRESS, "gpio_output_map": gpio_output_map}
        self.mcp23008_driver = mcp23008(bus, kwargs)

    def turn_on(self):
        self.mcp23008_driver.turn_on_relay(self.component.gpio)

    def turn_off(self):
        self.mcp23008_driver.turn_off_relay(self.component.gpio)

    def is_on(self) -> int:
        try:
            result = self.mcp23008_driver.get_single_gpio_status(self.component.gpio)
        except:
            return I2CErrorEnum.READ_ERROR
        if not property_format.is_bit(result):
            raise Exception(f"{ MakeModel.NCD__PR814SPST} returned {result}, expected 0 or 1!")
        return int(result)
