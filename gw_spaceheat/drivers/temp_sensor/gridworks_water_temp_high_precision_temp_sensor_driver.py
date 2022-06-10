import random
import time

from data_classes.components.temp_sensor_component import TempSensorComponent
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel


class GridworksWaterTempSensorHighPrecision_TempSensorDriver(TempSensorDriver):
    BASE_READ_TIME_MS = 879
    READ_TIME_FUZZ_MULTIPLIER = 6
    MEAN_READ_TIME_MS = BASE_READ_TIME_MS + (READ_TIME_FUZZ_MULTIPLIER / 2)

    def __init__(self, component: TempSensorComponent):
        super(GridworksWaterTempSensorHighPrecision_TempSensorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            raise Exception(f"Expected GridWorks__WaterTempHighPrecision, got {component.cac}")

    def read_temp(self):
        reading_time_ms = self.BASE_READ_TIME_MS + int(self.READ_TIME_FUZZ_MULTIPLIER * random.random())
        temp_f_times_1000 = 67000 + int(500 * random.random())
        time.sleep(reading_time_ms / 1000)
        return temp_f_times_1000
