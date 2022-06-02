import threading
import time

from actors.sensor.sensor_base import SensorBase
from data_classes.cacs.temp_sensor_cac import TempSensorCac
from data_classes.sh_node import ShNode
from drivers.temp_sensor.adafruit_642__temp_sensor_driver import \
    Adafruit642_TempSensorDriver
from drivers.temp_sensor.gridworks_water_temp_high_precision_temp_sensor_driver import \
    GridworksWaterTempSensorHighPrecision_TempSensorDriver
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_base import TelemetryName
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import \
    GtTelemetry101_Maker


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
        self.consume_thread.start()
        self.sensing_thread = threading.Thread(target=self.main)
        self.sensing_thread.start()

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
            raise Exception(f"TelemetryName for {self.cac.temp_unit} and precision exponent of"
                            f"{self.cac.precision_exponent} not set yet!")

    def publish(self):
        payload = GtTelemetry101_Maker(name=self.telemetry_name.value,
                                       value=int(self.temp),
                                       scada_read_time_unix_ms=int(time.time() * 1000)).type
        self.publish_gt_telemetry_1_0_1(payload)
        
    def consume(self):
        pass

    def main(self):
        while True:
            self.temp = self.driver.read_temp()
            self.publish()
