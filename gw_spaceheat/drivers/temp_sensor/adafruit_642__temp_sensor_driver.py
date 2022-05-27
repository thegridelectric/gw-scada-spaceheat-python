""" driver code for Adafruit 642 High Temp Waterproof DS18B20 Digital temp sensor """

import time
import os
import platform

import schema.property_format as property_format

from data_classes.components.temp_sensor_component import TempSensorComponent
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver

BASE_DIR = '/sys/bus/w1/devices/'
ONE_WIRE_FILE_START_ID = '28'


class Adafruit642_TempSensorDriver(TempSensorDriver):

    def __init__(self, component: TempSensorComponent):
        super(Adafruit642_TempSensorDriver,self).__init__(component=component)
        if component.cac.make_model != 'Adafruit__642':
            raise Exception(f"Expected Adafruit__642, got {component.cac}")
        property_format.check_is_64_bit_hex(component.hw_uid)

    def read_temp_raw(self):
        if platform.system() == 'Darwin':
            raise Exception(f"Calling onewire from a mac! Check component ....")
        all_driver_data_folders = list(filter(lambda x: x.startswith(ONE_WIRE_FILE_START_ID),[x[1] for x in os.walk(BASE_DIR)][0]))
        candidate_driver_data_folders = list(filter(lambda x: x.endswith(self.component.hw_uid), all_driver_data_folders))
        if len(candidate_driver_data_folders) != 1:
            raise Exception(f"looking for unique folder ending in {self.component.hw_uid}. Found {candidate_driver_data_folders}")
        device_folder = candidate_driver_data_folders[0]
        device_file = device_folder + '/w1_slave'
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def read_temp(self) -> int:
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c_times_1000 = int(temp_string) 
        return temp_c_times_1000

