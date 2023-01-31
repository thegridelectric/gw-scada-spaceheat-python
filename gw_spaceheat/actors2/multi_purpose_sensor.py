"""Implements MultipurposeSensor via SyncThreadActor and MultipurposeSensorDriverThread.
A helper class, MultipurposeSensorSetupHelper,
isolates code used only in  MultipurposeSensorDriverThread constructor. """

import time
import typing
from collections import OrderedDict
from typing import Dict
from typing import List
from typing import Optional

from gwproto import Message
from gwproto.enums import TelemetryName

from actors2.actor import SyncThreadActor
from actors2.message import GsPwrMessage
from actors2.message import MultipurposeSensorTelemetryMessage
from actors2.scada_interface import ScadaInterface
from actors2.config import ScadaSettings
from data_classes.components.multipurpose_sensor_component import  MultipurposeSensorComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode


from named_tuples.telemetry_tuple import TelemetryTuple, unit_from_telemetry_name, exponent_from_telemetry_name
from proactor.sync_thread import SyncAsyncInteractionThread
from problems import Problems
from schema.enums import MakeModel

from schema.gt.telemetry_reporting_config.telemetry_reporting_config_maker import (
    TelemetryReportingConfig,
    TelemetryReportingConfig_Maker,
)

from drivers.multipurpose_sensor.multipurpose_sensor_driver import MultipurposeSensorDriver
from drivers.multipurpose_sensor.gridworks_tsnap1__multipurpose_sensor_driver import (
    GridworksTsnap1_MultipurposeSensorDriver,
)
from drivers.multipurpose_sensor.unknown_multipurpose_sensor_driver import UnknownMultipurposeSensorDriver

class MpDriverThreadSetupHelper:
    """A helper class to isolate code only used in construction of MultipurposeSensorDriverThread"""

    FASTEST_POLL_PERIOD_MS = 40
    DEFAULT_ASYNC_REPORTING_THRESHOLD = 0.05

    node: ShNode
    settings: ScadaSettings
    hardware_layout: HardwareLayout
    component: MultipurposeSensorComponent

    def __init__(
        self,
        node: ShNode,
        settings: ScadaSettings,
        hardware_layout: HardwareLayout,
    ):
        if not isinstance(node.component, MultipurposeSensorComponent):
            raise ValueError(
                "ERROR. PowerMeterDriverThread requires node with  MultipurposeSensorComponent. "
                f"Received node {node.alias} with componet type {type(node.component)}"
            )
        self.node = node
        self.settings = settings
        self.hardware_layout = hardware_layout
        self.component = typing.cast(MultipurposeSensorComponent, node.component)
        self.cac = self.component.cac
        self.poll_period_ms = max(
                self.FASTEST_POLL_PERIOD_MS,
                self.component.cac.poll_period_ms,
            )

    def make_reporting_config(self) -> Dict[TelemetryTuple, TelemetryReportingConfig]:
        config: Dict[TelemetryTuple, TelemetryReportingConfig] = OrderedDict()
        for node_name in self.component.about_node_name_list:
            idx = self.component.about_node_name_list.index(node_name)
            about_node = self.hardware_layout.node(node_name)
            telemetry_name = self.component.telemetry_name_list[idx]
            config[
                TelemetryTuple(
                    AboutNode=about_node,
                    SensorNode=self.node,
                    TelemetryName=self.component.telemetry_name_list[idx],
                )
            ] = TelemetryReportingConfig_Maker(
                about_node_name=about_node.alias,
                report_on_change=True,
                telemetry_name=telemetry_name,
                unit=unit_from_telemetry_name(telemetry_name),
                exponent=exponent_from_telemetry_name(telemetry_name),
                sample_period_s=self.component.sample_period_s_list[idx],
            ).tuple
        return config


    def make_driver(self) -> MultipurposeSensorDriver:
        if self.cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver = UnknownMultipurposeSensorDriver(component=self.component, settings=self.settings)
        elif self.cac.make_model == MakeModel.GRIDWORKS__TSNAP1:
            driver = GridworksTsnap1_MultipurposeSensorDriver(component=self.component, settings=self.settings)
        else:
            raise NotImplementedError(
                f"No ElectricMeter driver yet for {self.cac.make_model}"
            )
        return driver


class PowerMeterDriverThread(SyncAsyncInteractionThread):

    reporting_config: Dict[TelemetryTuple, TelemetryReportingConfig]
    driver: MultipurposeSensorDriver
    nameplate_telemetry_value: Dict[TelemetryTuple, int]
    last_reported_telemetry_value: Dict[TelemetryTuple, Optional[int]]
    latest_telemetry_value: Dict[TelemetryTuple, Optional[int]]
    _last_sampled_s: Dict[TelemetryTuple, Optional[int]]
    async_power_reporting_threshold: float
    _telemetry_destination: str
    _hardware_layout: HardwareLayout

    def __init__(
        self,
        node: ShNode,
        settings: ScadaSettings,
        hardware_layout: HardwareLayout,
        telemetry_destination: str,
        responsive_sleep_step_seconds=0.01,
        daemon: bool = True,
    ):
        super().__init__(
            name=node.alias,
            responsive_sleep_step_seconds=responsive_sleep_step_seconds,
            daemon=daemon,
        )
        self._hardware_layout = hardware_layout
        self._telemetry_destination = telemetry_destination
        setup_helper = MpDriverThreadSetupHelper(node, settings, hardware_layout)
        self.reporting_config = setup_helper.make_reporting_config()

        self.driver = setup_helper.make_driver()
        self.last_reported_telemetry_value = {
            tt: None for tt in self._hardware_layout.all_power_meter_telemetry_tuples
        }
        self.latest_telemetry_value = {
            tt: None for tt in self._hardware_layout.all_power_meter_telemetry_tuples
        }
        self._last_sampled_s = {
            tt: None for tt in self._hardware_layout.all_power_meter_telemetry_tuples
        }
        self.async_power_reporting_threshold = settings.async_power_reporting_threshold

    def _report_problems(self, problems: Problems, tag: str):
        self._put_to_async_queue(
            Message(
                Payload=problems.problem_event(
                    summary=f"Driver problems: {tag} for {self.driver.component}",
                    src=str(self.driver.component)
                )
            )
        )

    def _preiterate(self) -> None:
        result = self.driver.start()
        if result.is_ok():
            if result.value.warnings:
                self._report_problems(Problems(warnings=result.value.warnings), "startup warning")
        else:
            self._report_problems(Problems(errors=result.err()), "startup error")

    def _iterate(self) -> None:
        start_s = time.time()
        self.update_latest_value_dicts()
        telemetry_tuple_report_list = [
            tpl
            for tpl in self._hardware_layout.all_power_meter_telemetry_tuples
            if self.should_report_telemetry_reading(tpl)
        ]
        if telemetry_tuple_report_list:
            self.report_sampled_telemetry_values(telemetry_tuple_report_list)
        sleep_time_ms = self.reporting_config.PollPeriodMs
        delta_ms = 1000 * (time.time() - start_s)
        if delta_ms < self.reporting_config.PollPeriodMs:
            sleep_time_ms -= delta_ms
        self._iterate_sleep_seconds = sleep_time_ms / 1000

    def update_latest_value_dicts(self):
        for tt in self._hardware_layout.all_power_meter_telemetry_tuples:
            read = self.driver.read_telemetry_value(tt.TelemetryName)
            if read.is_ok():
                self.latest_telemetry_value[tt] = read.value.value
                if read.value.warnings:
                    self._report_problems(Problems(warnings=read.value.warnings), "read warnings")
            else:
                raise read.value

    def report_sampled_telemetry_values(
        self, telemetry_sample_report_list: List[TelemetryTuple]
    ):
        self._put_to_async_queue(
            MultipurposeSensorTelemetryMessage(
                src=self.name,
                dst=self._telemetry_destination,
                about_node_alias_list=list(
                    map(lambda x: x.AboutNode.alias, telemetry_sample_report_list)
                ),
                value_list=list(
                    map(
                        lambda x: self.latest_telemetry_value[x],
                        telemetry_sample_report_list,
                    )
                ),
                telemetry_name_list=list(
                    map(lambda x: x.TelemetryName, telemetry_sample_report_list)
                ),
            )
        )
        for tt in telemetry_sample_report_list:
            self._last_sampled_s[tt] = int(time.time())
            self.last_reported_telemetry_value[tt] = self.latest_telemetry_value[tt]

    def value_exceeds_async_threshold(self, telemetry_tuple: TelemetryTuple) -> bool:
        """This telemetry tuple is supposed to report asynchronously on change, with
        the amount of change required (as a function of the absolute max value) determined
        in the EqConfig.
        """
        # redo once MultipurposeSensorComponent is refactored to have a list of TelemetryReportingConfigs
        # config = self.reporting_config[telemetry_tuple]
        # if config.AsyncReportThreshold is None:
        #     return False
        # last_reported_value = self.last_reported_telemetry_value[telemetry_tuple]
        # latest_telemetry_value = self.latest_telemetry_value[telemetry_tuple]
        # abs_telemetry_delta = abs(latest_telemetry_value - last_reported_value)
        # max_telemetry_value = self.nameplate_telemetry_value[telemetry_tuple]
        # change_ratio = abs_telemetry_delta / max_telemetry_value
        # if change_ratio > config.AsyncReportThreshold:
        #     return True
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
        if (
            self._last_sampled_s[telemetry_tuple] is None
            or self.last_reported_telemetry_value[telemetry_tuple] is None
        ):
            return True
        if (
            time.time() - self._last_sampled_s[telemetry_tuple]
            > self.eq_reporting_config[telemetry_tuple].SamplePeriodS
        ):
            return True
        if self.value_exceeds_async_threshold(telemetry_tuple):
            return True
        return False

    @property
    def latest_agg_power_w(self) -> Optional[int]:
        """Tracks the sum of the power of the all the nodes whose power is getting measured by the power meter"""
        latest_power_list = [
            v
            for k, v in self.latest_telemetry_value.items()
            if k in self._hardware_layout.all_power_tuples
        ]
        if None in latest_power_list:
            return None
        return int(sum(latest_power_list))



class PowerMeter(SyncThreadActor):
    def __init__(
        self,
        name: str,
        services: ScadaInterface,
        settings: Optional[ScadaSettings] = None,
    ):

        super().__init__(
            name=name,
            services=services,
            sync_thread=PowerMeterDriverThread(
                node=services.hardware_layout.node(name),
                settings=services.settings if settings is None else settings,
                hardware_layout=services.hardware_layout,
                telemetry_destination=services.name,
            ),
        )
