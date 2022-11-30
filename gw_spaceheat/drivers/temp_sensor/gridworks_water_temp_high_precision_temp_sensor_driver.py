import random
import time
from typing import Optional

from data_classes.components.temp_sensor_component import TempSensorComponent
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel
from schema.enums.unit.unit_map import Unit


class GridworksWaterTempSensorHighPrecision_TempSensorDriver(TempSensorDriver):
    READ_TIME_FUZZ_MULTIPLIER = 6

    def __init__(self, component: TempSensorComponent):
        super(GridworksWaterTempSensorHighPrecision_TempSensorDriver, self).__init__(
            component=component
        )
        if component.cac.make_model != MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            raise Exception(f"Expected GridWorks__WaterTempHighPrecision, got {component.cac}")
        if component.cac.temp_unit == Unit.FAHRENHEIT:
            self._fake_temp_times_1000 = 67000
        elif component.cac.temp_unit == Unit.CELCIUS:
            self._fake_temp_times_1000 = 19444
        else:
            raise Exception(f"TempSensor unit {component.cac.temp_unit} not recognized!")

    def cmd_delay(self):
        typical_delay_ms = self.component.cac.typical_response_time_ms
        read_delay_ms = typical_delay_ms + int(self.READ_TIME_FUZZ_MULTIPLIER * random.random())
        time.sleep(read_delay_ms / 1000)

    def read_telemetry_value(self) -> int:
        self.cmd_delay()
        self._fake_temp_times_1000 += 250 - int(500 * random.random())
        return self._fake_temp_times_1000
