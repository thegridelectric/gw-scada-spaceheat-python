import time
from typing import Dict, List

import settings

from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from data_classes.sh_node import ShNode
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver import \
    GridworksSimBool30AmpRelay_BooleanActuatorDriver
from drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver import \
    NcdPr814Spst_BooleanActuatorDriver
from schema.enums.make_model.make_model_map import MakeModel
from schema.enums.role.role_map import Role
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_telemetry.gt_telemetry_maker import (GtTelemetry,
                                                       GtTelemetry_Maker)
from schema.gt.gt_sensor_reporting_config.gt_sensor_reporting_config_maker \
    import (GtSensorReportingConfig as ReportingConfig,
            GtSensorReportingConfig_Maker as ConfigMaker)
from schema.gt.gt_spaceheat_sync_single.gt_spaceheat_sync_single_maker \
    import GtSpaceheatSyncSingle_Maker
from schema.gt.gt_spaceheat_status.gt_spaceheat_status_maker \
    import GtSpaceheatStatus_Maker

from actors.scada_base import ScadaBase
from actors.utils import QOS, Subscription


class Scada(ScadaBase):

    def __init__(self, node: ShNode):
        super(Scada, self).__init__(node=node)
        self.power = 0
        self.total_power_w = 0
        self.driver: Dict[ShNode, BooleanActuatorDriver] = {}
        self.reporting_config: Dict[ShNode, ReportingConfig] = {}
        self.set_reporting_configs()
        self.latest_readings: Dict[ShNode, List] = {}
        self.latest_sample_times: Dict[ShNode, List] = {}
        self.flush_latest_readings()
        self.set_actuator_components()
        self.screen_print(f'Initialized {self.__class__}')

    def flush_latest_readings(self):
        for node in self.my_tank_water_temp_sensors():
            self.latest_readings[node] = []
            self.latest_sample_times[node] = []

    def set_reporting_configs(self):
        for node in self.my_tank_water_temp_sensors():
            cac = node.temp_sensor_component.cac
            if node.reporting_sample_period_s is None:
                raise Exception(f"Temp sensor node {node} is missing ReportingSamplePeriodS!")
            reporting_config = ConfigMaker(report_on_change=False,
                                           exponent=cac.reporting_exponent,
                                           reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
                                           sample_period_s=node.reporting_sample_period_s,
                                           telemetry_name=cac.telemetry_name,
                                           unit=cac.temp_unit,
                                           async_report_threshold=None).tuple
            self.reporting_config[node] = reporting_config

    def set_actuator_components(self):
        self.boost_actuator = ShNode.by_alias['a.elt1.relay']
        if self.boost_actuator.component.make_model == MakeModel.NCD__PR814SPST:
            self.driver[self.boost_actuator] = NcdPr814Spst_BooleanActuatorDriver(
                component=self.boost_actuator.component)
        elif self.boost_actuator.component.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver[self.boost_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(
                component=self.boost_actuator.component)
        else:
            raise NotImplementedError(f"No driver yet for {self.boost_actuator.component.make_model}")

        self.pump_actuator = ShNode.by_alias['a.tank.out.pump.relay']

        if self.pump_actuator.component.make_model == MakeModel.NCD__PR814SPST:
            self.driver[self.pump_actuator] = NcdPr814Spst_BooleanActuatorDriver(
                component=self.pump_actuator.component)
        elif self.pump_actuator.component.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver[self.pump_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(
                component=self.pump_actuator.component)
        else:
            raise NotImplementedError(f"No driver yet for {self.pump_actuator.component.make_model}")

    ################################################
    # Receiving messages
    ###############################################

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [Subscription(Topic=f'a.m/{GsPwr_Maker.type_alias}', Qos=QOS.AtMostOnce),
                            Subscription(Topic=f'a.tank.out.flowmeter1/{GtTelemetry_Maker.type_alias}',
                            Qos=QOS.AtLeastOnce)]
        for node in self.my_tank_water_temp_sensors():
            my_subscriptions.append(Subscription(Topic=f'{node.alias}/{GtTelemetry_Maker.type_alias}',
                                    Qos=QOS.AtLeastOnce))
        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        self.screen_print("Got message")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
        elif isinstance(payload, GtTelemetry):
            self.gt_telemetry_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias['a.m']:
            raise Exception("Need to track all metering and make sure we have the sum")
        self.screen_print(f"Got {payload}")
        self.total_power_w = payload.Power
        self.gw_publish(payload=payload)

    def gt_telemetry_received(self, from_node: ShNode, payload: GtTelemetry):
        self.screen_print(f"{payload.Value} from {from_node.alias}")
        if from_node not in self.latest_readings.keys():
            self.screen_print(f"Not tracking readings from {from_node}!")
            return
        self.latest_readings[from_node].append(payload.Value)
        self.latest_sample_times[from_node].append(payload.ScadaReadTimeUnixMs)

    def on_gw_message(self, from_node: ShNode, payload: GtTelemetry):
        if from_node != ShNode.by_alias['a']:
            raise Exception("gw messages must come from the remote AtomicTNode!")
        if isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_dispatch_received(self, from_node: ShNode, payload: GsDispatch):
        raise NotImplementedError

    ################################################
    # Primary functions
    ###############################################

    def turn_on(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_on()

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_off()

    def send_status(self):
        self.screen_print("Should send status")
        node = ShNode.by_alias['a.tank.temp0']
        first_read_time_unix_s = int(self.latest_sample_times[node][0] / 1000)
        sync = GtSpaceheatSyncSingle_Maker(first_read_time_unix_s=first_read_time_unix_s,
                                           sample_period_s=self.reporting_config[node].SamplePeriodS,
                                           sh_node_alias=node.alias,
                                           telemetry_name=self.reporting_config[node].TelemetryName,
                                           value_list=self.latest_readings[node]).tuple
        slot_start_unix_s = self._last_5_cron_s
        status_payload = GtSpaceheatStatus_Maker(about_g_node_alias=settings.TA_G_NODE_ALIAS,
                                                 slot_start_unix_s=slot_start_unix_s,
                                                 reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
                                                 async_status_list=[],
                                                 sync_status_list=[sync]).tuple
        self.latest_status_payload = status_payload
        self.gw_publish(payload=status_payload)
        self.flush_latest_readings()

    def cron_every_5(self):
        self.send_status()
        self._last_5_cron_s = int(time.time())

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            if self.time_for_5_cron():
                self.cron_every_5()
            time.sleep(1)

    def my_tank_water_temp_sensors(self) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes))
