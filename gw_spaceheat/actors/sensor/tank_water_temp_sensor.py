import time
import threading
import csv
import pendulum
from typing import List
from actors.sensor.sensor_base import SensorBase

from data_classes.components.sensor_component import SensorComponent
from data_classes.cacs.temp_sensor_cac import TempSensorCac
from data_classes.sh_node import ShNode
from data_classes.sh_node_role_static import SENSOR
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_base import TelemetryName
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import GtTelemetry101_Maker
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from drivers.temp_sensor.adafruit_642__temp_sensor_driver import Adafruit642_TempSensorDriver
from drivers.temp_sensor.gridworks_water_temp_high_precision_temp_sensor_driver import GridworksWaterTempSensorHighPrecision_TempSensorDriver


class TankWaterTempSensor(SensorBase):
    def __init__(self, node: ShNode):
        super(TankWaterTempSensor, self).__init__(node=node)   
        self.temp = 67123
        self.screen_print('hi')
        self.driver: TempSensorDriver = None
        self.cac: TempSensorCac = self.node.primary_component.cac
        self.set_driver()
        self.telemetry_name: TelemetryName = None
        self.set_telemetry_name()
        self.temp_readings: List = []
        self.out_file = f'tmp_{node.alias}.csv'
        self.screen_print("writing output header")
        with open(self.out_file, 'w') as outfile:
            write = csv.writer(outfile, delimiter=',')
            write.writerow(['TimeUtc', 't_unix_s', 'ms', 'alias', 'WaterTempCTimes1000'])
        self.consume_thread.start()
        self.sensing_thread = threading.Thread(target=self.main)
        self.sensing_thread.start()
        self.local_log_thread = threading.Thread(target=self.log_temp)
        self.local_log_thread.start()
         
    def log_temp(self):
        while True:
            time.sleep(60)
            self.screen_print("appending output")
            with open(self.out_file, 'a') as outfile:
                write = csv.writer(outfile, delimiter=',')
                for row in self.temp_readings:
                    write.writerow(row)
            self.temp_readings = []

    def set_driver(self):
        if self.node.primary_component.cac.make_model == 'Adafruit__642':
            self.driver = Adafruit642_TempSensorDriver(component=self.node.primary_component)
        elif self.node.primary_component.cac.make_model == 'GridWorks__WaterTempHighPrecision':
            self.driver = GridworksWaterTempSensorHighPrecision_TempSensorDriver(component=self.node.primary_component)

    def set_telemetry_name(self):
        if self.cac.temp_unit == 'F' and self.cac.precision_exponent == 3:
            self.telemetry_name = TelemetryName.WATER_TEMP_F_TIMES_1000
        elif self.cac.temp_unit == 'C' and self.cac.precision_exponent == 3:
            self.telemetry_name = TelemetryName.WATER_TEMP_C_TIMES_1000
        else:
            raise Exception(f"TelemetryName for {self.cac.temp_unit} and precision exponent of {self.cac.precision_exponent} not set yet!")

    def publish(self):
        payload = GtTelemetry101_Maker(name=self.telemetry_name.value,
                        value=int(self.temp),
                        scada_read_time_unix_ms=int(time.time()*1000)).type
        self.publish_gt_telemetry_1_0_1(payload)
        
    def consume(self):
        pass

    def main(self):
        while True:
            self.temp = self.driver.read_temp()
            t_unix_float = int(time.time())
            t_unix_s = int(t_unix_float)
            ms = int(t_unix_float*1000) % 1000
            t = pendulum.from_timestamp(t_unix_s)
            self.temp_readings.append([t.strftime("%Y-%m-%d %H:%M:%S"),t_unix_s, ms, self.node.alias, self.temp])
            self.publish()
