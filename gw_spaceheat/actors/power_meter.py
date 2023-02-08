import datetime
import time
import typing
from typing import Dict
from typing import List
from typing import Optional

from gwproto.enums import TelemetryName
from gwproto.messages import GsPwr_Maker
from gwproto.messages import GtShTelemetryFromMultipurposeSensor_Maker

from actors.actor_base import ActorBase
from actors.utils import Subscription
from actors.utils import responsive_sleep
from actors2.config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.components.resistive_heater_component import ResistiveHeaterComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import (
    GridworksSimPm1_PowerMeterDriver,
)
from drivers.power_meter.openenergy_emonpi__power_meter_driver import (
    OpenenergyEmonpi_PowerMeterDriver,
)
from drivers.power_meter.power_meter_driver import PowerMeterDriver
from drivers.power_meter.schneiderelectric_iem3455__power_meter_driver import (
    SchneiderElectricIem3455_PowerMeterDriver,
)
from drivers.power_meter.unknown_power_meter_driver import UnknownPowerMeterDriver
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums import MakeModel
from schema.enums import Role
from schema.enums import Unit

from schema.gt.telemetry_reporting_config.telemetry_reporting_config_maker import (
    TelemetryReportingConfig,
    TelemetryReportingConfig_Maker,
)

from schema.gt.gt_powermeter_reporting_config.gt_powermeter_reporting_config_maker import (
    GtPowermeterReportingConfig as ReportingConfig,
)
from schema.gt.gt_powermeter_reporting_config.gt_powermeter_reporting_config_maker import (
    GtPowermeterReportingConfig_Maker as ReportingConfig_Maker,
)


class PowerMeter(ActorBase):

    """PowerMetering operates independently of dispatch. That is, polling the
    power readings occurs frequently (e.g. every 40 ms to every second) and independently
    of dispatch instructions. Power is reported asynchronously on change.

    Other electrical quantities (frequency, current, voltage) are reported according
    to configuration."""

    FASTEST_POWER_METER_POLL_PERIOD_MS = 40

    @classmethod
    def get_resistive_heater_nameplate_power_w(cls, node: ShNode) -> int:
        if node.role != Role.BOOST_ELEMENT:
            raise Exception("This function should only be called for nodes that are boost elements")
        component: ResistiveHeaterComponent = typing.cast(ResistiveHeaterComponent, node.component)
        cac = component.cac
        return cac.nameplate_max_power_w

    @classmethod
    def get_resistive_heater_nameplate_current_amps(cls, node: ShNode) -> float:
        """Note that all ShNodes of role BOOST_ELEMENT must have a non-zero RatedVoltageV and have a component
        of type ResistiveHeaterComponent.  Likewise, all ResistiveHeaterCacs have a positive NamePlateMaxPower.
        This is enforced by schema and not checked here."""
        if node.role != Role.BOOST_ELEMENT:
            raise Exception("This function should only be called for nodes that are boost elements")
        component: ResistiveHeaterComponent = typing.cast(ResistiveHeaterComponent, node.component)
        cac = component.cac
        return cac.nameplate_max_power_w / node.rated_voltage_v

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        super(PowerMeter, self).__init__(alias=alias, settings=settings, hardware_layout=hardware_layout)
        if self.node != self.power_meter_node():
            raise Exception(
                f"PowerMeter node must be the unique Spaceheat Node of role PowerMeter! Not {self.node}"
            )

        self.eq_reporting_config: Dict[TelemetryTuple, TelemetryReportingConfig] = {}
        self.reporting_config: ReportingConfig = self.set_reporting_config(
            component=typing.cast(ElectricMeterComponent, self.node.component)
        )
        self.driver: PowerMeterDriver = self.set_power_meter_driver(component=self.node.component)
        self.driver.start()

        self.nameplate_telemetry_value: Dict[
            TelemetryTuple, int
        ] = self.get_nameplate_telemetry_value()

        self.last_reported_agg_power_w: Optional[int] = None

        self.last_reported_telemetry_value: Dict[TelemetryTuple, Optional[int]] = {
            tt: None for tt in self.all_power_meter_telemetry_tuples()
        }
        self.latest_telemetry_value: Dict[TelemetryTuple, Optional[int]] = {
            tt: None for tt in self.all_power_meter_telemetry_tuples()
        }

        self._last_sampled_s: Dict[TelemetryTuple, Optional[int]] = {
            tt: None for tt in self.all_power_meter_telemetry_tuples()
        }

        # self.check_hw_uid()
        self.screen_print(f"Initialized {self.__class__}")

    ###################################
    # Initializing configuration
    ###################################

    def set_power_meter_driver(self, component: ElectricMeterComponent) -> PowerMeterDriver:
        cac = component.cac
        if cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver = UnknownPowerMeterDriver(component=component, settings=self.settings)
        elif cac.make_model == MakeModel.SCHNEIDERELECTRIC__IEM3455:
            driver = SchneiderElectricIem3455_PowerMeterDriver(component=component, settings=self.settings)
        elif cac.make_model == MakeModel.GRIDWORKS__SIMPM1:
            driver = GridworksSimPm1_PowerMeterDriver(component=component, settings=self.settings)
        elif cac.make_model == MakeModel.OPENENERGY__EMONPI:
            driver = OpenenergyEmonpi_PowerMeterDriver(component=component, settings=self.settings)
        else:
            raise NotImplementedError(f"No ElectricMeter driver yet for {cac.make_model}")
        return driver

    def set_reporting_config(self, component: ElectricMeterComponent) -> ReportingConfig:
        cac = component.cac
        eq_reporting_config_list = []
        for about_node in self.all_metered_nodes():
            current_config = TelemetryReportingConfig_Maker(
                about_node_name=about_node.alias,
                report_on_change=True,
                telemetry_name=TelemetryName.CURRENT_RMS_MICRO_AMPS,
                unit=Unit.AMPS_RMS,
                nameplate_max_value=1000,
                exponent=6,
                sample_period_s=self.settings.seconds_per_report,
                async_report_threshold=self.settings.async_power_reporting_threshold
            ).tuple
            tt = TelemetryTuple(
                AboutNode=about_node,
                SensorNode=self.node,
                TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
            )
            eq_reporting_config_list.append(current_config)
            self.eq_reporting_config[tt] = current_config

            power_config = TelemetryReportingConfig_Maker(
                about_node_name=about_node.alias,
                report_on_change=True,
                telemetry_name=TelemetryName.POWER_W,
                unit=Unit.W,
                nameplate_max_value=1000,
                exponent=0,
                sample_period_s=self.settings.seconds_per_report,
                async_report_threshold=self.settings.async_power_reporting_threshold
            ).tuple
            eq_reporting_config_list.append(power_config)
            tt = TelemetryTuple(
                AboutNode=about_node, SensorNode=self.node, TelemetryName=TelemetryName.POWER_W
            )
            self.eq_reporting_config[tt] = power_config

        if cac.update_period_ms is None:
            poll_period_ms = self.FASTEST_POWER_METER_POLL_PERIOD_MS
        else:
            poll_period_ms = max(self.FASTEST_POWER_METER_POLL_PERIOD_MS, cac.update_period_ms)
        return ReportingConfig_Maker(
            reporting_period_s=self.settings.seconds_per_report,
            poll_period_ms=poll_period_ms,
            hw_uid=component.hw_uid,
            electrical_quantity_reporting_config_list=eq_reporting_config_list,
        ).tuple

    def get_nameplate_telemetry_value(self) -> Dict[TelemetryTuple, int]:
        response_dict: Dict[TelemetryTuple, int] = {}
        for about_node in self.all_resistive_heaters():
            current_tt = TelemetryTuple(
                AboutNode=about_node,
                SensorNode=self.node,
                TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
            )
            nameplate_current_amps = self.get_resistive_heater_nameplate_current_amps(
                node=about_node
            )
            response_dict[current_tt] = int(10**6 * nameplate_current_amps)

            power_tt = TelemetryTuple(
                AboutNode=about_node, SensorNode=self.node, TelemetryName=TelemetryName.POWER_W
            )
            nameplate_power_w = self.get_resistive_heater_nameplate_power_w(node=about_node)
            response_dict[power_tt] = int(nameplate_power_w)
        return response_dict

    def check_hw_uid(self):
        result = self.driver.read_hw_uid()
        if result.is_ok():
            if self.reporting_config.HwUid != result.value.value:
                raise Exception(
                    f"HwUid associated to component {self.reporting_config.HwUid} "
                    f"does not match HwUid read by driver {result.value.value}"
                )
        else:
            raise result.value

    ###############################
    # Stubs for receiving MQTT messages
    ################################

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, from_node: ShNode, payload):
        pass

    ###############################
    # Core functions
    ################################

    def update_latest_value_dicts(self):
        for tt in self.all_power_meter_telemetry_tuples():
            read = self.driver.read_telemetry_value(tt.TelemetryName)
            if read.is_ok():
                self.latest_telemetry_value[tt] = read.value.value
            else:
                raise read.value

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
        for tt in telemetry_sample_report_list:
            self._last_sampled_s[tt] = int(time.time())
            self.last_reported_telemetry_value[tt] = self.latest_telemetry_value[tt]

    def value_exceeds_async_threshold(self, telemetry_tuple: TelemetryTuple) -> bool:
        """This telemetry tuple is supposed to report asynchronously on change, with
        the amount of change required (as a function of the absolute max value) determined
        in the EqConfig.
        """
        telemetry_reporting_config = self.eq_reporting_config[telemetry_tuple]
        last_reported_value = self.last_reported_telemetry_value[telemetry_tuple]
        latest_telemetry_value = self.latest_telemetry_value[telemetry_tuple]
        abs_telemetry_delta = abs(latest_telemetry_value - last_reported_value)
        max_telemetry_value = self.nameplate_telemetry_value[telemetry_tuple]
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
            v for k, v in self.latest_telemetry_value.items() if k in self.all_power_tuples()
        ]
        if None in latest_power_list:
            return None
        return int(sum(latest_power_list))

    @property
    def nameplate_agg_power_w(self) -> int:
        nameplate_power_list = [
            v for k, v in self.nameplate_telemetry_value.items() if k in self.all_power_tuples()
        ]
        return int(sum(nameplate_power_list))

    def report_aggregated_power_w(self):
        self.publish(GsPwr_Maker(power=self.latest_agg_power_w).tuple)
        self.last_reported_agg_power_w = self.latest_agg_power_w
        self.screen_print(f"{datetime.datetime.now().isoformat()} {self.latest_agg_power_w} W")

    def should_report_aggregated_power(self) -> bool:
        """Aggregated power is sent up asynchronously on change via a GsPwr message, and the last aggregated
        power sent up is recorded in self.last_reported_agg_power_w."""
        if self.latest_agg_power_w is None:
            return False
        if self.last_reported_agg_power_w is None:
            return True
        abs_power_delta = abs(self.latest_agg_power_w - self.last_reported_agg_power_w)
        change_ratio = abs_power_delta / self.nameplate_agg_power_w
        if change_ratio > self.settings.async_power_reporting_threshold:
            return True
        return False

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            start_s = time.time()
            self.update_latest_value_dicts()
            if self.should_report_aggregated_power():
                self.report_aggregated_power_w()
            telemetry_tuple_report_list: List[TelemetryTuple] = []
            for telemetry_tuple in self.all_power_meter_telemetry_tuples():
                if self.should_report_telemetry_reading(telemetry_tuple):
                    telemetry_tuple_report_list.append(telemetry_tuple)
            if len(telemetry_tuple_report_list) > 0:
                self.report_sampled_telemetry_values(telemetry_tuple_report_list)
            sleep_time_ms = self.reporting_config.PollPeriodMs / 5
            delta_ms = 1000 * (time.time() - start_s)
            if delta_ms < self.reporting_config.PollPeriodMs:
                sleep_time_ms -= delta_ms
            responsive_sleep(self, sleep_time_ms / 1000)
