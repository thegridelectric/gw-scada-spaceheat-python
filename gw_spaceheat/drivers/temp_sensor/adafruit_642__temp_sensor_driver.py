""" driver code for Adafruit 642 High Temp Waterproof DS18B20 Digital temp sensor """

import os
import platform
import time
from typing import Optional
import schema.property_format as property_format
from data_classes.components.temp_sensor_component import TempSensorComponent
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel

BASE_DIR = "/sys/bus/w1/devices/"
ONE_WIRE_FILE_START_ID = "28"

DEFAULT_BAD_TEMP_C_TIMES_1000_VALUE = 10 ** 6
class Adafruit642_TempSensorDriver(TempSensorDriver):
    def __init__(self, component: TempSensorComponent):
        super(Adafruit642_TempSensorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.ADAFRUIT__642:
            raise Exception(f"Expected Adafruit__642, got {component.cac}")
        property_format.is_64_bit_hex(component.hw_uid)

    def read_temp_c_times_1000(self) -> Optional[int]:
        if platform.system() == "Darwin":
            raise Exception("Calling onewire from a mac! Check component ....")
        all_driver_data_folders = list(
            filter(
                lambda x: x.startswith(ONE_WIRE_FILE_START_ID), [x[1] for x in os.walk(BASE_DIR)][0]
            )
        )
        candidate_driver_data_folders = list(
            filter(lambda x: x.endswith(self.component.hw_uid), all_driver_data_folders)
        )
        if len(candidate_driver_data_folders) != 1:
            # raise Exception(
            #     f"looking for unique folder ending in {self.component.hw_uid}."
            #     f" Found {candidate_driver_data_folders}"
            # )
            return None
        device_folder = BASE_DIR + candidate_driver_data_folders[0]
        device_file = device_folder + "/w1_slave"
        try:
            f = open(device_file, "r")
        except:
            return None
        try:
            lines = f.readlines()
        except:
            f.close()
            return None
        f.close()
        try:
            equals_pos = lines[1].find("t=")
        except:
            return None
            
        if equals_pos == -1:
            return None
        try:
            temp_string = lines[1][equals_pos + 2 :]
        except:
            return None
        temp_c_times_1000 = int(temp_string)
        return temp_c_times_1000

    def read_telemetry_value(self) -> int:
        temp_c_times_1000 = self.read_temp_c_times_1000()
        i = 0
        while temp_c_times_1000 is None:
            time.sleep(0.2)
            temp_c_times_1000  = self.read_temp_c_times_1000()
            i += 1
            if i == 10:
                return DEFAULT_BAD_TEMP_C_TIMES_1000_VALUE

        return temp_c_times_1000
