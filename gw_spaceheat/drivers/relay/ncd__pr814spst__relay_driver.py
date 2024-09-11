from typing import Optional

import smbus2 as smbus
from actors.config import ScadaSettings
from drivers.driver_result import DriverResult
from drivers.exceptions import DriverWarning
from drivers.relay.mcp23008.mcp_driver import mcp23008
from drivers.relay.relay_driver import RelayDriver
from enums import MakeModel
from gwproto.data_classes.components.relay_component import RelayComponent
from result import Err, Ok, Result
from gwproto import property_format


class NcdPr814SpstI2cReadWarning(DriverWarning):
    ...


class NcdPr814SpstI2cStartupFailure(DriverWarning):
    ...


COMPONENT_I2C_ADDRESS = 0x20


class NcdPr814Spst_RelayDriver(RelayDriver):
    mcp23008_driver: Optional[mcp23008] = None
    last_val: int = 0

    def __init__(self, component: RelayComponent, settings: ScadaSettings):
        super(NcdPr814Spst_RelayDriver, self).__init__(
            component=component, settings=settings
        )
        if component.cac.MakeModel != MakeModel.NCD__PR814SPST:
            raise Exception(f"Expected {MakeModel.NCD__PR814SPST}, got {component.cac}")

    def turn_on(self):
        if self.mcp23008_driver is not None:
            if self.component.normally_open:
                self.mcp23008_driver.energize_relay(self.component.gpio)
            else:
                self.mcp23008_driver.deenergize_relay(self.component.gpio)

    def turn_off(self):
        if self.mcp23008_driver is not None:
            if self.component.normally_open:
                self.mcp23008_driver.deenergize_relay(self.component.gpio)
            else:
                self.mcp23008_driver.energize_relay(self.component.gpio)

    def start(self) -> Result[DriverResult[bool], Exception]:
        driver_result = DriverResult(True)
        try:
            bus = smbus.SMBus(1)
            gpio_output_map = {0, 1, 2, 3}
            kwargs = {
                "address": COMPONENT_I2C_ADDRESS,
                "gpio_output_map": gpio_output_map,
            }
            self.mcp23008_driver = mcp23008(bus, kwargs)
            if self.component.normally_open:
                self.last_val = 0
            else:
                self.last_val = 1
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
                active = self.mcp23008_driver.relay_is_activated(
                    self.component.gpio
                )
                if not self.component.normally_open:
                    active = not active
                driver_result.value = int(active)
                self.last_val = driver_result.value
            except Exception as e:
                driver_result.warnings.append(e)
            if not property_format.is_bit(driver_result.value):
                driver_result.warnings.append(
                    Exception(
                        f"{MakeModel.NCD__PR814SPST} returned {driver_result.value}, expected 0 or 1!"
                    )
                )
                driver_result.value = None
        return Ok(driver_result)
