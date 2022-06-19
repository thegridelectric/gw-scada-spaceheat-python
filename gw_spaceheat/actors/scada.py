import time
from typing import Dict, List, Optional

import pendulum
import helpers
import settings
from data_classes.node_config import NodeConfig
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role
from schema.gs.gs_dispatch_maker import GsDispatch
from schema.gt.gt_dispatch.gt_dispatch_maker import GtDispatch, GtDispatch_Maker
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status_maker import \
    GtShSimpleSingleStatus_Maker, GtShSimpleSingleStatus
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import \
    GtShSimpleStatus_Maker

from schema.gt.gt_telemetry.gt_telemetry_maker import (GtTelemetry,
                                                       GtTelemetry_Maker)

from actors.scada_base import ScadaBase
from actors.utils import QOS, Subscription


class Scada(ScadaBase):

    def __init__(self, node: ShNode, logging_on=False):
        super(Scada, self).__init__(node=node, logging_on=logging_on)
        now = int(time.time())
        self._last_5_cron_s = (now - (now % 300))
        self.power = 0
        self.total_power_w = 0
        self.config: Dict[ShNode, NodeConfig] = {}
        self.set_node_configs()
        self.latest_readings: Dict[ShNode, List] = {}
        self.latest_sample_times_ms: Dict[ShNode, List] = {}
        self.flush_latest_readings()
        self.screen_print(f'Initialized {self.__class__}')

    def flush_latest_readings(self):
        for node in self.my_tank_water_temp_sensors() + self.my_boolean_actuators():
            self.latest_readings[node] = []
            self.latest_sample_times_ms[node] = []

    def set_node_configs(self):
        all_nodes = list(ShNode.by_alias.values())
        for node in all_nodes:
            self.config[node] = NodeConfig(node)

    ################################################
    # Receiving messages
    ###############################################

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [Subscription(Topic=f'a.m/{GsPwr_Maker.type_alias}', Qos=QOS.AtMostOnce)]

        for node in self.my_tank_water_temp_sensors() + self.my_boolean_actuators():
            my_subscriptions.append(Subscription(Topic=f'{node.alias}/{GtTelemetry_Maker.type_alias}',
                                    Qos=QOS.AtLeastOnce))
        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GsDispatch):
            self.gt_dispatch_received(from_node, payload)
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
        if from_node not in self.latest_readings.keys():
            self.screen_print(f"Not tracking readings from {from_node}!")
            return
        self.latest_readings[from_node].append(payload.Value)
        self.latest_sample_times_ms[from_node].append(payload.ScadaReadTimeUnixMs)

    def on_gw_message(self, from_node: ShNode, payload: GtTelemetry):
        if from_node != ShNode.by_alias['a']:
            raise Exception("gw messages must come from the remote AtomicTNode!")
        if isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
        elif isinstance(payload, GtDispatch):
            self.gt_dispatch_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_dispatch_received(self, from_node: ShNode, payload: GsDispatch):
        raise NotImplementedError

    def gt_dispatch_received(self, from_node: ShNode, payload: GtDispatch):
        self.screen_print(f"received {payload} from {from_node}")
        if payload.ShNodeAlias not in ShNode.by_alias.keys():
            self.screen_print(f"dispatch received for unknnown sh_node {payload.ShNodeAlias}")
            return
        ba = ShNode.by_alias[payload.ShNodeAlias]
        if not isinstance(ba.component, BooleanActuatorComponent):
            self.screen_print(f"{ba} must be a BooleanActuator!")
            return
        if payload.RelayState == 1:
            self.turn_on(ba)
            self.screen_print(f"Dispatched {ba.alias}  on")
        else:
            self.turn_off(ba)
            self.screen_print(f"Dispatched {ba.alias} off")

    ################################################
    # Primary functions
    ###############################################

    def turn_on(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            dispatch_payload = GtDispatch_Maker(relay_state=1,
                                                sh_node_alias=ba.alias).tuple
            self.publish(payload=dispatch_payload)
            self.screen_print(f"Sent {dispatch_payload}")
        else:
            self.config[ba].driver.turn_on()

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            dispatch_payload = GtDispatch_Maker(relay_state=0,
                                                sh_node_alias=ba.alias).tuple
            self.publish(payload=dispatch_payload)
        else:
            self.config[ba].driver.turn_off()

    def make_single_status(self, node: ShNode) -> Optional[GtShSimpleSingleStatus]:
        if node not in self.latest_sample_times_ms.keys():
            raise Exception(f'{node} missing from self.lastest_sample-times')
        if len(self.latest_readings[node]) == 0:
            return None
        read_time_unix_ms_list = self.latest_sample_times_ms[node]
        value_list = self.latest_readings[node]
        telemetry_name = self.config[node].reporting.TelemetryName
        return GtShSimpleSingleStatus_Maker(sh_node_alias=node.alias,
                                            telemetry_name=telemetry_name,
                                            value_list=value_list,
                                            read_time_unix_ms_list=read_time_unix_ms_list,
                                            ).tuple

    def send_status(self):
        self.screen_print("Should send status")
        simple_single_status_list = []
        for node in (self.my_tank_water_temp_sensors() + self.my_boolean_actuators()):
            single_status = self.make_single_status(node)
            if single_status:
                simple_single_status_list.append(self.make_single_status(node))

        slot_start_unix_s = self._last_5_cron_s
        payload = GtShSimpleStatus_Maker(about_g_node_alias=helpers.ta_g_node_alias(),
                                         slot_start_unix_s=slot_start_unix_s,
                                         reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
                                         simple_single_status_list=simple_single_status_list,
                                         ).tuple

        self.gw_publish(payload)
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
            if int(time.time()) % 30 == 0:
                self.screen_print(f"{pendulum.from_timestamp(int(time.time()))}")
                self.screen_print(f"{self.next_5_cron_s - int(time.time())} seconds till status")

    def my_tank_water_temp_sensors(self) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes))

    def my_boolean_actuators(self) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: x.role == Role.BOOLEAN_ACTUATOR, all_nodes))

    @property
    def next_5_cron_s(self) -> int:
        last_cron_s = self._last_5_cron_s - (self._last_5_cron_s % 300)
        return last_cron_s + 300

    def time_for_5_cron(self) -> bool:
        if time.time() > self.next_5_cron_s:
            return True
        return False
