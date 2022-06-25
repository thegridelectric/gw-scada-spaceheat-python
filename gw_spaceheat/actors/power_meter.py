import time
from typing import List, Optional, Dict

from data_classes.node_config import NodeConfig
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import (
    GtShTelemetryFromMultipurposeSensor_Maker,
)

from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config import GtEqReportingConfig
from actors.actor_base import ActorBase
from actors.utils import Subscription, responsive_sleep


class PowerMeter(ActorBase):
    def __init__(self, node: ShNode, logging_on=False):
        super(PowerMeter, self).__init__(node=node, logging_on=logging_on)
        self.my_telemetry_tuple = TelemetryTuple(
            AboutNode=ShNode.by_alias["a.elt1"],
            SensorNode=self.node,
            TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
        )
        self.config = NodeConfig(self.node)
        self.driver = self.config.driver
        self.check_hw_uid()

        self.max_telemetry_value: Dict[TelemetryTuple, Optional[int]] = {
            self.my_telemetry_tuple: 10**7
        }

        self.prev_telemetry_value: Dict[TelemetryTuple, Optional[int]] = {
            self.my_telemetry_tuple: None
        }
        self.latest_telemetry_value: Dict[TelemetryTuple, Optional[int]] = {
            self.my_telemetry_tuple: None
        }
        self.eq_config: Dict[TelemetryTuple, GtEqReportingConfig] = {}
        self.initialize_eq_config()
        self._last_sampled_s: Dict[TelemetryTuple, Optional[int]] = {self.my_telemetry_tuple: None}

        self.screen_print(f"Initialized {self.__class__}")

    def initialize_eq_config(self):
        all_eq_configs = self.config.reporting.EqReportingConfigList
        amp_list = list(
            filter(
                lambda x: x.TelemetryName == TelemetryName.CURRENT_RMS_MICRO_AMPS
                and x.ShNodeAlias == "a.elt1",
                all_eq_configs,
            )
        )
        self.eq_config[self.my_telemetry_tuple] = amp_list[0]

    def my_telemetry_tuples(self) -> List[TelemetryTuple]:
        return [self.my_telemetry_tuple]

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, from_node: ShNode, payload):
        pass

    def check_hw_uid(self):
        if self.config.reporting.HwUid != self.driver.read_hw_uid():
            raise Exception(
                f"HwUid associated to component {self.config.reporting.HwUid} "
                f"does not match HwUid read by driver {self.driver.read_hw_uid()}"
            )

    def update_prev_and_latest_value_dicts(self):
        for tt in self.my_telemetry_tuples():
            self.prev_telemetry_value[tt] = self.latest_telemetry_value[tt]
            result = self.driver.read_current_rms_micro_amps()
            if not isinstance(result, int):
                raise Exception(f"{self.driver} returned {result}, expected int!")
            self.latest_telemetry_value[tt] = result

    def report_sampled_telemetry_values(self, telemetry_sample_report_list: List[TelemetryTuple]):
        about_node_alias_list = list(map(lambda x: x.AboutNode.alias, telemetry_sample_report_list))
        telemetry_name_list = list(map(lambda x: x.TelemetryName, telemetry_sample_report_list))
        value_list = list(
            map(lambda x: self.latest_telemetry_value[x], telemetry_sample_report_list)
        )

        payload = GtShTelemetryFromMultipurposeSensor_Maker(
            about_node_alias_list=about_node_alias_list,
            value_list=value_list,
            telemetry_name_list=telemetry_name_list,
            scada_read_time_unix_ms=int(1000 * time.time()),
        ).tuple
        self.publish(payload)
        self.payload = payload
        for tt in telemetry_sample_report_list:
            self._last_sampled_s[tt] = int(time.time())

    def value_exceeds_async_threshold(self, telemetry_tuple: TelemetryTuple) -> bool:
        """This telemetry tuple is supposed to report asynchronously on change, with
        the amount of change required (as a function of the absolute max value) determined
        in the EqConfig.
        """
        telemetry_reporting_config = self.eq_config[telemetry_tuple]
        prev_telemetry_value = self.prev_telemetry_value[telemetry_tuple]
        latest_telemetry_value = self.latest_telemetry_value[telemetry_tuple]
        abs_telemetry_delta = abs(latest_telemetry_value - prev_telemetry_value)
        max_telemetry_value = self.max_telemetry_value[telemetry_tuple]
        change_ratio = abs_telemetry_delta / max_telemetry_value
        if change_ratio > telemetry_reporting_config.AsyncReportThreshold:
            return True
        return False

    def should_report_telemetry_reading(self, telemetry_tuple: TelemetryTuple) -> bool:
        """The telemetry data should get reported synchronously once every SamplePeriodS, and also asynchronously
        on a big enough change - both configured in the eq_config (eq for electrical quantity) config for this
        telemetry tuple.

        Note that SamplePeriodS will often be 300 seconds, which will also match the duration of each status message
        the Scada sends up to the cloud (GtShSimpleStatus.ReportingPeriodS).  The Scada will likely do this at the
        top of every 5 minutes - but not the power meter.. The point of the synchronous reporting is to
        get at least one reading for this telemetry tuple in the Scada's status report; it does not need to be
        at the beginning or end of the status report time period.
        """
        if self.latest_telemetry_value[telemetry_tuple] is None:
            return False
        if self._last_sampled_s[telemetry_tuple] is None:
            return True
        if time.time() - self._last_sampled_s[telemetry_tuple] > self.eq_config[telemetry_tuple].SamplePeriodS:
            return True
        if self.value_exceeds_async_threshold(telemetry_tuple):
            return True
        return False

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            start_s = time.time()
            self.update_prev_and_latest_value_dicts()
            telemetry_tuple_report_list: List[TelemetryTuple] = []
            for telemetry_tuple in self.my_telemetry_tuples():
                if self.should_report_telemetry_reading(telemetry_tuple):
                    telemetry_tuple_report_list.append(telemetry_tuple)
            if len(telemetry_tuple_report_list) > 0:
                self.report_sampled_telemetry_values(telemetry_tuple_report_list)
                self.screen_print(
                    f"{self.my_telemetry_tuple.TelemetryName.value} for "
                    f" {self.my_telemetry_tuple.AboutNode.alias} is "
                    f"{self.latest_telemetry_value[self.my_telemetry_tuple]}"
                )
            delta_ms = 1000 * (time.time() - start_s)
            if delta_ms < self.config.reporting.PollPeriodMs:
                sleep_time_ms = self.config.reporting.PollPeriodMs - delta_ms
            responsive_sleep(self, sleep_time_ms / 1000)
