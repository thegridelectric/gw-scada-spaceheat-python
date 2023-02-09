from enum import Enum
import importlib
import schema.property_format as property_format

from actors2.config import ScadaSettings
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.base.mcp23008 import mcp23008
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from schema.enums import MakeModel

COMPONENT_I2C_ADDRESS = 0x20

DRIVER_IS_REAL = True
for module_name in [
    "smbus2"
]:
    found = importlib.util.find_spec(module_name)
    if found is None:
        DRIVER_IS_REAL = False
        break
    import smbus2 as smbus
    try:
        bus = smbus.SMBus(1)
    except FileNotFoundError:
        DRIVER_IS_REAL = False
        break

class I2CErrorEnum(Enum):
    NO_ADDRESS_ERROR = -100000
    READ_ERROR = -200000


if DRIVER_IS_REAL:

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
else:
    class NcdPr814Spst_BooleanActuatorDriver(BooleanActuatorDriver):
        def __init__(self, component: BooleanActuatorComponent, settings: ScadaSettings):
            super(NcdPr814Spst_BooleanActuatorDriver, self).__init__(component=component, settings=settings)

        def turn_on(self):
            raise NotImplementedError

        def turn_off(self):
            raise NotImplementedError

        def is_on(self):
            raise NotImplementedError
