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
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker

from schema.enums.make_model.make_model_map import MakeModel


class TankWaterTempSensor(SensorBase):
    def __init__(self, node: ShNode):
        super(TankWaterTempSensor, self).__init__(node=node)   
        self.temp = 67123
        self.driver: TempSensorDriver = None
        self.cac: TempSensorCac = self.node.primary_component.cac
        self.set_driver()
        self.telemetry_name: TelemetryName = None
        self.set_telemetry_name()
        self.sensing_thread = threading.Thread(target=self.main)
        self.sensing_thread.start()
        self.consume()
        self.screen_print(f'Started {self.__class__}')

    def set_driver(self):
        if self.node.primary_component.make_model == MakeModel.ADAFRUIT__642:
            self.driver = Adafruit642_TempSensorDriver(component=self.node.primary_component)
        elif self.node.primary_component.make_model == MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            self.driver = GridworksWaterTempSensorHighPrecision_TempSensorDriver(component=self.node.primary_component)

    def set_telemetry_name(self):
        if self.cac.temp_unit == 'F' and self.cac.precision_exponent == 3:
            self.telemetry_name = TelemetryName.WATER_TEMP_F_TIMES1000
        elif self.cac.temp_unit == 'C' and self.cac.precision_exponent == 3:
            self.telemetry_name = TelemetryName.WATER_TEMP_C_TIMES1000
        else:
            raise Exception(f"TelemetryName for {self.cac.temp_unit} and precision exponent of"
                            f"{self.cac.precision_exponent} not set yet!")

    def publish(self):
        payload = GtTelemetry_Maker(name=self.telemetry_name,
                                    value=int(self.temp),
                                    exponent=0,
                                    scada_read_time_unix_ms=int(time.time() * 1000)).tuple
        self.publish_gt_telemetry(payload)

    def consume(self):
        pass

    def terminate_sensing(self):
        self._sensing = False

    def main(self):
        self._sensing = True
        while self._sensing == True:
            self.temp = self.driver.read_temp()
            self.publish()
