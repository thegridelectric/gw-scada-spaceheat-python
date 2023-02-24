from typing import Optional

import smbus2 as smbus
from result import Err
from result import Ok
from result import Result

import schema.property_format as property_format

from actors2.config import ScadaSettings
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from drivers.base.mcp23008 import mcp23008
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from drivers.driver_result import DriverResult
from drivers.exceptions import DriverWarning
from schema.enums import MakeModel

class NcdPr814SpstI2cReadWarning(DriverWarning):
    ...

class NcdPr814SpstI2cStartupFailure(DriverWarning):
    ...


COMPONENT_I2C_ADDRESS = 0x20

class NcdPr814Spst_BooleanActuatorDriver(BooleanActuatorDriver):
    mcp23008_driver: Optional[mcp23008] = None
    last_val: int = 0

    def __init__(self, component: BooleanActuatorComponent, settings: ScadaSettings):
        super(NcdPr814Spst_BooleanActuatorDriver, self).__init__(component=component, settings=settings)
        if component.cac.make_model != MakeModel.NCD__PR814SPST:
            raise Exception(f"Expected {MakeModel.NCD__PR814SPST}, got {component.cac}")

    def turn_on(self):
        if self.mcp23008_driver is not None:
            self.mcp23008_driver.turn_on_relay(self.component.gpio)

    def turn_off(self):
        if self.mcp23008_driver is not None:
            self.mcp23008_driver.turn_off_relay(self.component.gpio)

    def start(self) -> Result[DriverResult[bool], Exception]:
        driver_result = DriverResult(True)
        try:
            bus = smbus.SMBus(1)
            gpio_output_map = {0, 1, 2, 3}
            kwargs = {"address": COMPONENT_I2C_ADDRESS, "gpio_output_map": gpio_output_map}
            self.mcp23008_driver = mcp23008(bus, kwargs)
            self.last_val = 0
        except Exception as e:
            driver_result.value = False
            driver_result.warnings.append(e)
            driver_result.warnings.append(NcdPr814SpstI2cStartupFailure())
        return Ok(driver_result)


    def is_on(self) -> Result[DriverResult[int | None], Exception]:
        driver_result = DriverResult[int | None](None)
        if self.mcp23008_driver is None:
            driver_result.value = None
        else:
            try:
               driver_result.value = self.mcp23008_driver.get_single_gpio_status(self.component.gpio)
               self.last_val = driver_result.value
            except Exception as e:
                driver_result.warnings.append(e)
            if not property_format.is_bit(driver_result.value):
                driver_result.warnings.append(
                    Exception(f"{MakeModel.NCD__PR814SPST} returned {driver_result.value}, expected 0 or 1!")
                )
                driver_result.value = None
        return Ok(driver_result)