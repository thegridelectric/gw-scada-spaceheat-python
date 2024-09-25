"""Implements MultipurposeSensor via SyncThreadActor and MultipurposeSensorDriverThread.
A helper class, MultipurposeSensorSetupHelper,
isolates code used only in  MultipurposeSensorDriverThread constructor. """
import importlib
import importlib.util
import sys
import time
import typing
from collections import OrderedDict
from typing import Dict, List, Optional

from actors.config import ScadaSettings
from actors.message import MultipurposeSensorTelemetryMessage
from actors.scada_interface import ScadaInterface
from gwproactor import SyncThreadActor
from gwproto.data_classes.components.ads111x_based_component import (
    Ads111xBasedComponent
)
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.sh_node import ShNode
from drivers.multipurpose_sensor.multipurpose_sensor_driver import (
    MultipurposeSensorDriver,
    TelemetrySpec,
)
from gwproto import Message

from gwproactor.message import InternalShutdownMessage
from gwproactor.sync_thread import SyncAsyncInteractionThread
from gwproactor import Problems
from enums import MakeModel
from gwproto.data_classes.data_channel import DataChannel
from gwproto.types import AdsChannelConfig

UNKNOWNMAKE__UNKNOWNMODEL__MODULE_NAME = "drivers.multipurpose_sensor.unknown_multipurpose_sensor_driver"
UNKNOWNMAKE__UNKNOWNMODEL__CLASS_NAME = "UnknownMultipurposeSensorDriver"


class MpDriverThreadSetupHelper:
    """A helper class to isolate code only used in construction of MultipurposeSensorDriverThread"""

    node: ShNode
    settings: ScadaSettings
    hardware_layout: HardwareLayout
    component: Ads111xBasedComponent

    def __init__(
        self,
        node: ShNode,
        settings: ScadaSettings,
        hardware_layout: HardwareLayout,
    ):
        if not isinstance(node.component, Ads111xBasedComponent):
            raise ValueError(
                "ERROR. MultipurposeSensorDriverThread requires node with  Ads111xBasedComponent. "
                f"Received node {node.alias} with componet type {type(node.component)}"
            )
        self.node = node
        self.settings = settings
        self.hardware_layout = hardware_layout
        self.component = typing.cast(Ads111xBasedComponent, node.component)

    def make_config_by_telemetry_spec(
        self,
    ) -> Dict[TelemetrySpec, AdsChannelConfig]:
        d: Dict[TelemetrySpec, AdsChannelConfig] = OrderedDict()
        for config in self.component.gt.ConfigList:
            terminal_block_idx = config.TerminalBlockIdx
            channel = self.hardware_layout.data_channels[config.ChannelName]
            ts = TelemetrySpec(AdsTerminalBlockIdx=terminal_block_idx, Type=channel.TelemetryName)
            d[ts] = config
        return d

    def make_driver(self) -> MultipurposeSensorDriver:
        driver_module_name = ""
        driver_class_name = ""
        cac = self.component.cac
        if cac.MakeModel == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver_module_name = UNKNOWNMAKE__UNKNOWNMODEL__MODULE_NAME
            driver_class_name = UNKNOWNMAKE__UNKNOWNMODEL__CLASS_NAME
        elif cac.MakeModel == MakeModel.GRIDWORKS__TSNAP1:
            driver_module_name = "drivers.multipurpose_sensor.gridworks_tsnap1__multipurpose_sensor_driver"
            driver_class_name = "GridworksTsnap1_MultipurposeSensorDriver"
            for module_name in [
                "board",
                "busio",
                "adafruit_ads1x15",
                "adafruit_ads1x15.ads1115",
                "adafruit_ads1x15.analog_in",
            ]:
                found = importlib.util.find_spec(module_name)
                if found is None:
                    driver_module_name = UNKNOWNMAKE__UNKNOWNMODEL__MODULE_NAME
                    driver_class_name = UNKNOWNMAKE__UNKNOWNMODEL__CLASS_NAME
                    break
        if not driver_module_name or not driver_class_name:
            raise NotImplementedError(
                f"No MultipurposeSensor driver yet for {cac.MakeModel}"
            )
        if driver_module_name not in sys.modules:
            importlib.import_module(driver_module_name)
        driver_class = getattr(sys.modules[driver_module_name], driver_class_name)
        return driver_class(component=self.component, settings=self.settings)


class MultipurposeSensorDriverThread(SyncAsyncInteractionThread):

    FASTEST_POLL_PERIOD_MS = 40
    driver: MultipurposeSensorDriver
    config_by_spec: Dict[TelemetrySpec, AdsChannelConfig]
    telemetry_specs: List[TelemetrySpec]
    my_channels: List[DataChannel]
    telemetry_configs: List[AdsChannelConfig]
    last_reported_telemetry_value: Dict[AdsChannelConfig, Optional[int]]
    latest_telemetry_value: Dict[AdsChannelConfig, Optional[int]]
    _last_sampled_s: Dict[AdsChannelConfig, Optional[int]]
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
        self.component = typing.cast(Ads111xBasedComponent, node.component)
        self.poll_period_ms = max(
            self.FASTEST_POLL_PERIOD_MS,
            self.component.cac.MinPollPeriodMs,
        )
        self._telemetry_destination = telemetry_destination
        my_channel_names = [x.ChannelName for x in self.component.gt.ConfigList]
        all_channels = self._hardware_layout.data_channels
        self.my_channels = [ch for ch in all_channels.values() if ch.AboutNodeName in my_channel_names]
        setup_helper = MpDriverThreadSetupHelper(node, settings, hardware_layout)
        self.config_by_spec = setup_helper.make_config_by_telemetry_spec()
        self.telemetry_specs = list(self.config_by_spec.keys())
        self.telemetry_configs = self.component.gt.ConfigList
        self.driver = setup_helper.make_driver()
        self.last_reported_telemetry_value = {tt: None for tt in self.telemetry_configs}
        self.latest_telemetry_value = {tc: None for tc in self.telemetry_configs}
        self._last_sampled_s = {tc: None for tc in self.telemetry_configs}
    

    def _report_problems(self, problems: Problems, tag: str):
        self._put_to_async_queue(
            Message(
                Payload=problems.problem_event(
                    summary=f"Driver problems: {tag} for {self.driver.component}",
                )
            )
        )

    def _preiterate(self) -> None:
        result = self.driver.start()
        if result.is_ok():
            if result.value.warnings:
                self._report_problems(
                    Problems(warnings=result.value.warnings), "startup warning"
                )
        else:
            self._report_problems(Problems(errors=[result.err()]), "startup error")
            self._put_to_async_queue(
                InternalShutdownMessage(Src=self.name, Reason=f"Driver start error for {self.name}")
            )

    def _iterate(self) -> None:
        start_s = time.time()
        self.poll_sensor()
        report_list = [
            tc
            for tc in self.telemetry_configs
            if self.should_report_telemetry_reading(tc)
        ]
        if report_list:
            self.report_sampled_telemetry_values(report_list)
        sleep_time_ms = self.poll_period_ms
        delta_ms = 1000 * (time.time() - start_s)
        if delta_ms < self.poll_period_ms:
            sleep_time_ms -= delta_ms
        self._iterate_sleep_seconds = sleep_time_ms / 1000

    def poll_sensor(self):
        read = self.driver.read_telemetry_values(self.telemetry_specs)
        if read.is_ok():
            reading_by_ts = read.value.value
            for ts in self.telemetry_specs:
                if ts in reading_by_ts:
                    telemetry_config = self.config_by_spec[ts]
                    self.latest_telemetry_value[telemetry_config] = reading_by_ts[ts]
            if read.value.warnings:
                self._report_problems(
                    Problems(warnings=read.value.warnings), "read warnings"
                )
        else:
            raise read.value
    

    def report_sampled_telemetry_values(
        self, report_list: List[AdsChannelConfig]
    ):
        about_names = [self._hardware_layout.data_channels[tc.ChannelName].AboutNodeName 
                        for tc in report_list]
        
        self._put_to_async_queue(
            MultipurposeSensorTelemetryMessage(
                src=self.name,
                dst=self._telemetry_destination,
                about_node_alias_list=about_names,
                value_list=list(
                    map(
                        lambda x: self.latest_telemetry_value[x],
                        report_list,
                    )
                ),
                telemetry_name_list=list(map(lambda x: x.TelemetryName, report_list)),
            )
        )
        for tt in report_list:
            self._last_sampled_s[tt] = int(time.time())
            self.last_reported_telemetry_value[tt] = self.latest_telemetry_value[tt]

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def value_exceeds_async_threshold(
        self, telemetry_config: AdsChannelConfig
    ) -> bool:
        """This telemetry tuple is supposed to report asynchronously on change, with
        the amount of change required (as a function of the absolute max value) determined
        in the EqConfig.
        """
        if (
                telemetry_config.AsyncCapture and
                telemetry_config.AsyncCaptureDelta is not None
        ):
            abs_telemetry_delta = abs(
                self.latest_telemetry_value[telemetry_config] -
                self.last_reported_telemetry_value[telemetry_config]
            )
            if abs_telemetry_delta > telemetry_config.AsyncCaptureDelta:
                return True
        return False

    def should_report_telemetry_reading(
        self, telemetry_config: AdsChannelConfig
    ) -> bool:
        if self.latest_telemetry_value[telemetry_config] is None:
            return False
        if (
            self._last_sampled_s[telemetry_config] is None
            or self.last_reported_telemetry_value[telemetry_config] is None
        ):
            return True
        if (
            time.time() - self._last_sampled_s[telemetry_config]
            > telemetry_config.CapturePeriodS
        ):
            return True
        if self.value_exceeds_async_threshold(telemetry_config):
            return True
        return False


class MultipurposeSensor(SyncThreadActor):
    def __init__(
        self,
        name: str,
        services: ScadaInterface,
        settings: Optional[ScadaSettings] = None,
    ):

        super().__init__(
            name=name,
            services=services,
            sync_thread=MultipurposeSensorDriverThread(
                node=services.hardware_layout.node(name),
                settings=services.settings if settings is None else settings,
                hardware_layout=services.hardware_layout,
                telemetry_destination=services.name,
            ),
        )
