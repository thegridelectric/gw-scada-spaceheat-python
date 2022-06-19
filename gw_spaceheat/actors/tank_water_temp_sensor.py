import time
from typing import List

from data_classes.node_config import NodeConfig
from data_classes.sh_node import ShNode
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker

from actors.actor_base import ActorBase
from actors.utils import Subscription


class TankWaterTempSensor(ActorBase):
    MAIN_LOOP_MIN_TIME_S = 0.2

    def __init__(self, node: ShNode, logging_on=False):
        super(TankWaterTempSensor, self).__init__(node=node, logging_on=logging_on)
        self._last_sent_s = 0
        self._sent_latest_sample = False
        self.temp = None
        self.config = NodeConfig(self.node)
        self.screen_print(f"Initialized {self.__class__}")

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, from_node: ShNode, payload):
        pass

    def check_and_report_temp(self):
        check_start_s = time.time()
        sample_period_s = self.config.reporting.SamplePeriodS
        telemetry_name = self.config.reporting.TelemetryName
        exponent = self.config.reporting.Exponent
        if int(check_start_s + self.config.typical_response_time_ms / 1000) % sample_period_s == 0:
            self.temp = self.config.driver.read_temp()
            time_of_read_s = time.time()
            if int(time_of_read_s) > self._last_sent_s:
                payload = GtTelemetry_Maker(
                    name=telemetry_name,
                    value=int(self.temp),
                    exponent=exponent,
                    scada_read_time_unix_ms=int(time_of_read_s * 1000),
                ).tuple
                self.publish(payload=payload)
                self.screen_print(f"{payload.Value} {telemetry_name.value}")
                # self.screen_print(f"{int(time_of_read_s * 1000)}")
                self._sent_latest_sample = True
                self._last_sent_s = int(time_of_read_s)
        else:
            time_of_read_s = check_start_s
        if (time_of_read_s - check_start_s) > self.MAIN_LOOP_MIN_TIME_S:
            return
        wait_time_s = self.MAIN_LOOP_MIN_TIME_S - (time_of_read_s - check_start_s)
        time.sleep(wait_time_s)

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            self.check_and_report_temp()
