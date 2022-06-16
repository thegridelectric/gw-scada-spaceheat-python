import time
from typing import List

import settings
from data_classes.errors import DataClassLoadingError
from data_classes.components.temp_sensor_component import TempSensorComponent
from data_classes.cacs.temp_sensor_cac import TempSensorCac
from data_classes.sh_node import ShNode
from drivers.temp_sensor.adafruit_642__temp_sensor_driver import \
    Adafruit642_TempSensorDriver
from drivers.temp_sensor.gridworks_water_temp_high_precision_temp_sensor_driver import \
    GridworksWaterTempSensorHighPrecision_TempSensorDriver
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel

from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker
from schema.gt.gt_sensor_reporting_config.gt_sensor_reporting_config_maker \
    import GtSensorReportingConfig, GtSensorReportingConfig_Maker as ConfigMaker
from actors.actor_base import ActorBase
from actors.utils import Subscription


class TankWaterTempSensor(ActorBase):
    def __init__(self, node: ShNode):
        super(TankWaterTempSensor, self).__init__(node=node)
        self.temp = 67123
        self.driver: TempSensorDriver = None
        self.cac: TempSensorCac = self.component.cac
        self.set_driver()
        self.telemetry_name = self.cac.telemetry_name
        self.reporting_config: GtSensorReportingConfig = None
        self.set_reporting_config()
        self.screen_print(f"Initialized {self.__class__}")

    def set_driver(self):
        if self.component.make_model == MakeModel.ADAFRUIT__642:
            self.driver = Adafruit642_TempSensorDriver(component=self.node.component)
        elif self.component.make_model == MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION:
            self.driver = GridworksWaterTempSensorHighPrecision_TempSensorDriver(component=self.node.component)

    def set_reporting_config(self):
        if self.node.reporting_sample_period_s is None:
            raise Exception(f"Temp sensor node {self.node} is missing ReportingSamplePeriodS!")
        self.reporting_config = ConfigMaker(report_on_change=False,
                                            exponent=self.cac.reporting_exponent,
                                            reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
                                            sample_period_s=self.node.reporting_sample_period_s,
                                            telemetry_name=self.cac.telemetry_name,
                                            unit=self.cac.temp_unit,
                                            async_report_threshold=None).tuple

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, from_node: ShNode, payload):
        pass

    def main(self):
        self._main_loop_running = True
        self._last_sent_s = 0
        while self._main_loop_running is True:
            now = time.time()
            if int(now + self.component.cac.typical_read_time_ms / 1000) % self.reporting_config.SamplePeriodS == 0:
                self.temp = self.driver.read_temp()
                now = time.time()
                if int(now) > self._last_sent_s:
                    payload = GtTelemetry_Maker(name=self.telemetry_name,
                                                value=int(self.temp),
                                                exponent=0,
                                                scada_read_time_unix_ms=int(now * 1000)).tuple
                    self.publish(payload=payload)
                    self.screen_print("Published!")
                    self._sent_latest_sample = True
                    self._last_sent_s = int(now)

    @property
    def component(self) -> TempSensorComponent:
        if self.node.component_id is None:
            return None
        if self.node.component_id not in TempSensorComponent.by_id.keys():
            raise DataClassLoadingError(f"{self.node.alias} component {self.node.component_id} \
                not in TempSensorComponents!")
        return TempSensorComponent.by_id[self.node.component_id]