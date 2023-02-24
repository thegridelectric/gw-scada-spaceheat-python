import sys
import time

from result import Err
from result import Ok
from result import Result

from drivers.driver_result import DriverResult
from drivers.exceptions import DriverWarning
from drivers.pipe_flow_sensor.ezflo.AtlasI2C import AtlasI2C
from actors2.config import ScadaSettings
from data_classes.components.pipe_flow_sensor_component import \
    PipeFlowSensorComponent
from drivers.pipe_flow_sensor.pipe_flow_sensor_driver import \
    PipeFlowSensorDriver
from problems import Problems
from schema.enums import MakeModel

class EZFlowI2cReadWarning(DriverWarning):
    ...

class EZFlowI2cAddressMissing(DriverWarning):
    address: int

    def __init__(
        self,
        address: int,
        msg: str = "",
    ):
        super().__init__(msg)
        self.address = address

    def __str__(self):
        s = self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" <{super_str}>"
        s += f"   address:0x{self.address:02X}"
        return s

class AtlasEzflo_PipeFlowSensorDriver(PipeFlowSensorDriver):
    dev: AtlasI2C
    _last_cumulative_gallons: int = 0

    def __init__(self, component: PipeFlowSensorComponent, settings: ScadaSettings):
        super(AtlasEzflo_PipeFlowSensorDriver, self).__init__(component=component, settings=settings)
        if self.component.cac.make_model != MakeModel.ATLAS__EZFLO:
            raise Exception(f"Expected {MakeModel.ATLAS__EZFLO}, got {component.cac}")

    def start(self) -> Result[DriverResult[bool], Exception]:
        device = AtlasI2C()
        device_address = self.component.i2c_address
        device.set_i2c_address(device_address)
        response = device.query("I")
        driver_result = DriverResult(True)
        try:
            moduletype = response.split(",")[1]
            name = device.query("name,?").split(",")[1]
        except IndexError:
            moduletype = ""
            name = ""
            driver_result.warnings.append(
                EZFlowI2cAddressMissing(
                    device_address,
                    msg=(
                        f">> WARNING: device at I2C address {device_address} "
                        " has not been identified as an EZO device, and will not be queried"
                    )
                ).with_traceback(sys.exc_info()[2])
            )
        self.dev = AtlasI2C(address=device_address, moduletype=moduletype, name=name)
        self._last_cumulative_gallons = 0
        cum_read = self.read_cumulative_gallons()
        if not cum_read.is_ok():
            return Err(
                Problems(
                    msg=f"ERROR in start()/read_cumulative_gallons() for {self.component.display_name}",
                    warnings=driver_result.warnings,
                    errors=[cum_read.err()]
                )
            )
        elif cum_read.value.value is not None:
            self._last_cumulative_gallons = cum_read.value.value
        driver_result.warnings.extend(cum_read.value.warnings)
        return Ok(driver_result)

    def __repr__(self):
        return f"Atlas Ezflo driver for {self.component.display_name}"

    def read_cumulative_gallons(self) -> Result[DriverResult[int | None], Exception]:
        time.sleep(1)
        self.dev.write("R")
        time.sleep(0.3)
        v0 = self.dev.read()
        driver_result = DriverResult(None)
        try:
            val = float(v0.split(':')[1].split('\x00')[0])
        except Exception as e:
            driver_result.warnings.append(EZFlowI2cReadWarning(
                f"<{e}> {type(e)}").with_traceback(sys.exc_info()[2]))
        else:
            driver_result.value = val
        return Ok(driver_result)

    def read_telemetry_value(self) -> Result[DriverResult[int | None], Exception]:
        cum_result = self.read_cumulative_gallons()
        if cum_result.is_ok() and cum_result.value.value is not None:
            cum_result.value = int(100 * cum_result.value.value * self.component.conversion_factor)
        return cum_result
