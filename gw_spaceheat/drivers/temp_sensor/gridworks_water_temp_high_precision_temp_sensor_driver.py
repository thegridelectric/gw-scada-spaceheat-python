import random
import time

from data_classes.components.temp_sensor_component import TempSensorComponent
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel


class GridworksWaterTempSensorHighPrecision_TempSensorDriver(TempSensorDriver):

    def __init__(self, component: TempSensorComponent):
        super(GridworksWaterTempSensorHighPrecision_TempSensorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            raise Exception(f"Expected GridWorks__WaterTempHighPrecision, got {component.cac}")

    def read_temp(self):
        reading_time_ms = 879 + int(6 * random.random())
        temp_f_times_1000 = 67000 + int(500 * random.random())
        time.sleep(reading_time_ms / 1000)
        return temp_f_times_1000
