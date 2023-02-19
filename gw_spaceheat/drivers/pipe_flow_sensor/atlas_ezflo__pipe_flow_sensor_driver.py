from typing import Optional
import time
from drivers.pipe_flow_sensor.ezflo.AtlasI2C import AtlasI2C
from actors2.config import ScadaSettings
from data_classes.components.pipe_flow_sensor_component import \
    PipeFlowSensorComponent
from drivers.pipe_flow_sensor.pipe_flow_sensor_driver import \
    PipeFlowSensorDriver
from schema.enums import MakeModel

class AtlasEzflo_PipeFlowSensorDriver(PipeFlowSensorDriver):
    def __init__(self, component: PipeFlowSensorComponent, settings: ScadaSettings):
        super(AtlasEzflo_PipeFlowSensorDriver, self).__init__(component=component, settings=settings)
        if self.component.cac.make_model != MakeModel.ATLAS__EZFLO:
            raise Exception(f"Expected {MakeModel.ATLAS__EZFLO}, got {component.cac}")
        device = AtlasI2C()
        device_address = self.component.i2c_address
        device.set_i2c_address(device_address)
        response = device.query("I")
        try:
            moduletype = response.split(",")[1]
            name = device.query("name,?").split(",")[1]
        except IndexError:
            print(">> WARNING: device at I2C address " + str(
                device_address) + " has not been identified as an EZO device, and will not be queried")
        self.dev = AtlasI2C(address=device_address, moduletype=moduletype, name=name)
        self._last_cumulative_gallons = 0
        cum_gallons = self.read_cumulative_gallons()
        if cum_gallons:
            self._last_cumulative_gallons = cum_gallons


    def __repr__(self):
        return f"Atlas Ezflo driver for {self.component.display_name}"

    def read_cumulative_gallons(self) -> Optional[int]:
        time.sleep(1)
        self.dev.write("R")
        time.sleep(0.3)
        v0 = self.dev.read()
        try:
            val = float(v0.split(':')[1].split('\x00')[0])
        except:
            print("Failed to get a reading")
            return None
        return val

    def read_telemetry_value(self) -> Optional[int]:
        cum = self.read_cumulative_gallons()
        if cum is None:
            return None
        return int(100 * cum * self.component.conversion_factor)


