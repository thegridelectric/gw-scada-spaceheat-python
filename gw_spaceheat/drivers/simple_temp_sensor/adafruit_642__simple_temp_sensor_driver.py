""" driver code for Adafruit 642 High Temp Waterproof DS18B20 Digital temp sensor """

import os
import platform
import time
from typing import Optional

from result import Ok
from result import Result

from actors.config import ScadaSettings
import schema.property_format as property_format
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from drivers.driver_result import DriverResult
from drivers.simple_temp_sensor.simple_temp_sensor_driver import SimpleTempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel

BASE_DIR = "/sys/bus/w1/devices/"
ONE_WIRE_FILE_START_ID = "28"

DEFAULT_BAD_TEMP_C_TIMES_1000_VALUE = 10 ** 6


class Adafruit642_SimpleTempSensorDriver(SimpleTempSensorDriver):
    def __init__(self, component: SimpleTempSensorComponent, settings: ScadaSettings):
        super(Adafruit642_SimpleTempSensorDriver, self).__init__(component=component, settings=settings)
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
        # noinspection PyBroadException
        try:
            f = open(device_file, "r")
        except:
            return None
        # noinspection PyBroadException
        try:
            lines = f.readlines()
        except:
            f.close()
            return None
        f.close()
        # noinspection PyBroadException
        try:
            equals_pos = lines[1].find("t=")
        except:
            return None

        if equals_pos == -1:
            return None
        # noinspection PyBroadException
        try:
            temp_string = lines[1][equals_pos + 2:]
        except:
            return None
        temp_c_times_1000 = int(temp_string)
        return temp_c_times_1000

    def read_telemetry_value(self) -> Result[DriverResult[int | None], Exception]:
        temp_c_times_1000 = self.read_temp_c_times_1000()
        i = 0
        while temp_c_times_1000 is None:
            time.sleep(0.2)
            temp_c_times_1000 = self.read_temp_c_times_1000()
            i += 1
            if i == 10:
                return Ok(DriverResult(DEFAULT_BAD_TEMP_C_TIMES_1000_VALUE))

        return Ok(DriverResult(temp_c_times_1000))

