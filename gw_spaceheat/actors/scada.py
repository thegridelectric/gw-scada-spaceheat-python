import enum
import time
from typing import Dict, List, Optional

import helpers
import pendulum
import settings
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.node_config import NodeConfig
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.role.role_map import Role
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName
from schema.gs.gs_dispatch_maker import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_dispatch.gt_dispatch_maker import GtDispatch, GtDispatch_Maker
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd_maker import (
    GtDriverBooleanactuatorCmd,
    GtDriverBooleanactuatorCmd_Maker,
)
from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status_maker import (
    GtShBooleanactuatorCmdStatus_Maker,
    GtShBooleanactuatorCmdStatus,
)
from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd_maker import GtShCliAtnCmd, GtShCliAtnCmd_Maker
from schema.gt.gt_sh_multipurpose_telemetry_status.gt_sh_multipurpose_telemetry_status_maker import (
    GtShMultipurposeTelemetryStatus_Maker,
    GtShMultipurposeTelemetryStatus,
)
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response_maker import (
    GtShCliScadaResponse_Maker,
)

from schema.gt.gt_sh_status.gt_sh_status_maker import GtShStatus_Maker

from schema.gt.gt_sh_simple_telemetry_status.gt_sh_simple_telemetry_status_maker import (
    GtShSimpleTelemetryStatus_Maker,
    GtShSimpleTelemetryStatus,
)

from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot_maker import (
    GtShStatusSnapshot,
    GtShStatusSnapshot_Maker,
)
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import (
    GtShTelemetryFromMultipurposeSensor,
    GtShTelemetryFromMultipurposeSensor_Maker,
)
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry, GtTelemetry_Maker

from actors.scada_base import ScadaBase
from actors.utils import QOS, Subscription, responsive_sleep


class ScadaCmdDiagnostic(enum.Enum):
    SUCCESS = "Success"
    PAYLOAD_NOT_IMPLEMENTED = "PayloadNotImplemented"
    DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR = "DispatchNodeNotBooleanActuator"


class Scada(ScadaBase):
    @classmethod
    def my_boolean_actuators(cls) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: (x.role == Role.BOOLEAN_ACTUATOR), all_nodes))

    @classmethod
    def my_simple_sensors(cls) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(
            filter(
                lambda x: (
                    x.role == Role.TANK_WATER_TEMP_SENSOR
                    or x.role == Role.BOOLEAN_ACTUATOR
                    or x.role == Role.PIPE_TEMP_SENSOR
                    or x.role == Role.PIPE_FLOW_METER
                ),
                all_nodes,
            )
        )

    @classmethod
    def my_multipurpose_sensors(cls) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: (x.role == Role.POWER_METER), all_nodes))

    def __init__(self, node: ShNode, logging_on=False):
        super(Scada, self).__init__(node=node, logging_on=logging_on)
        now = int(time.time())
        self._last_5_cron_s = now - (now % 300)
        self.power = 0
        self.total_power_w = 0
        self.config: Dict[ShNode, NodeConfig] = {}
        self.init_node_configs()
        self.latest_simple_value: Dict[ShNode, int] = {
            node: None for node in self.my_simple_sensors()
        }
        self.recent_simple_values: Dict[ShNode, List] = {
            node: [] for node in self.my_simple_sensors()
        }
        self.recent_simple_read_times_unix_ms: Dict[ShNode, List] = {
            node: [] for node in self.my_simple_sensors()
        }

        self.latest_value_from_multipurpose_sensor: Dict[TelemetryTuple, int] = {
            tt: None for tt in self.my_telemetry_tuples()
        }
        self.recent_values_from_multipurpose_sensor: Dict[TelemetryTuple, List] = {
            tt: [] for tt in self.my_telemetry_tuples()
        }
        self.recent_read_times_unix_ms_from_multipurpose_sensor: Dict[TelemetryTuple, List] = {
            tt: [] for tt in self.my_telemetry_tuples()
        }
        self.recent_ba_cmds: Dict[ShNode, List] = {node: [] for node in self.my_boolean_actuators()}

        self.recent_ba_cmd_times_unix_ms: Dict[ShNode, List] = {
            node: [] for node in self.my_boolean_actuators()
        }

        self.flush_latest_readings()
        self.screen_print(f"Initialized {self.__class__}")

    def flush_latest_readings(self):
        self.recent_simple_values = {node: [] for node in self.my_simple_sensors()}
        self.recent_simple_read_times_unix_ms = {node: [] for node in self.my_simple_sensors()}

        self.recent_values_from_multipurpose_sensor = {tt: [] for tt in self.my_telemetry_tuples()}
        self.recent_read_times_unix_ms_from_multipurpose_sensor = {
            tt: [] for tt in self.my_telemetry_tuples()
        }

        self.recent_ba_cmds = {node: [] for node in self.my_boolean_actuators()}
        self.recent_ba_cmd_times_unix_ms = {node: [] for node in self.my_boolean_actuators()}

    def init_node_configs(self):
        for node in self.my_simple_sensors():
            self.config[node] = NodeConfig(node)

    def my_telemetry_tuples(self) -> List[TelemetryTuple]:
        my_tuples = []
        example_tuple = TelemetryTuple(
            AboutNode=ShNode.by_alias["a.elt1"],
            SensorNode=ShNode.by_alias["a.m"],
            TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
        )
        my_tuples.append(example_tuple)
        return my_tuples

    ################################################
    # Receiving messages
    ###############################################

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [Subscription(Topic=f"a.m/{GsPwr_Maker.type_alias}", Qos=QOS.AtMostOnce)]

        for node in self.my_simple_sensors():
            my_subscriptions.append(
                Subscription(
                    Topic=f"{node.alias}/{GtTelemetry_Maker.type_alias}",
                    Qos=QOS.AtLeastOnce,
                )
            )
        for node in self.my_multipurpose_sensors():
            my_subscriptions.append(
                Subscription(
                    Topic=f"{node.alias}/{GtShTelemetryFromMultipurposeSensor_Maker.type_alias}",
                    Qos=QOS.AtLeastOnce,
                )
            )

        for node in self.my_boolean_actuators():
            my_subscriptions.append(
                Subscription(
                    Topic=f"{node.alias}/{GtDriverBooleanactuatorCmd_Maker.type_alias}",
                    Qos=QOS.AtLeastOnce,
                )
            )

        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
        elif isinstance(payload, GtDispatch):
            self.gt_dispatch_received(from_node, payload)
        elif isinstance(payload, GtTelemetry):
            self.gt_telemetry_received(from_node, payload),
        elif isinstance(payload, GtShTelemetryFromMultipurposeSensor):
            self.gt_sh_telemetry_from_multipurpose_sensor_received(from_node, payload)
        elif isinstance(payload, GtDriverBooleanactuatorCmd):
            self.gt_driver_booleanactuator_cmd_record_received(from_node, payload)
        else:
            raise Exception(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias["a.m"]:
            raise Exception("Need to track all metering and make sure we have the sum")
        self.total_power_w = payload.Power
        self.gw_publish(payload=payload)

    def gt_sh_telemetry_from_multipurpose_sensor_received(
        self, from_node: ShNode, payload: GtShTelemetryFromMultipurposeSensor
    ):
        if from_node in self.my_multipurpose_sensors():
            about_node_alias_list = payload.AboutNodeAliasList
            for about_alias in about_node_alias_list:
                if about_alias not in ShNode.by_alias.keys():
                    raise Exception(
                        f"alias {about_alias} in payload.AboutNodeAliasList not a recognized ShNode!"
                    )
                idx = about_node_alias_list.index(about_alias)
                tt = TelemetryTuple(
                    AboutNode=ShNode.by_alias[about_alias],
                    SensorNode=from_node,
                    TelemetryName=payload.TelemetryNameList[idx],
                )
                if tt not in self.my_telemetry_tuples():
                    raise Exception(f"Scada not tracking telemetry tuple {tt}!")
                self.recent_values_from_multipurpose_sensor[tt].append(payload.ValueList[idx])
                self.recent_read_times_unix_ms_from_multipurpose_sensor[tt].append(
                    payload.ScadaReadTimeUnixMs
                )
                self.latest_value_from_multipurpose_sensor[tt] = payload.ValueList[idx]

    def gt_telemetry_received(self, from_node: ShNode, payload: GtTelemetry):
        if from_node in self.my_simple_sensors():
            self.recent_simple_values[from_node].append(payload.Value)
            self.recent_simple_read_times_unix_ms[from_node].append(payload.ScadaReadTimeUnixMs)
            self.latest_simple_value[from_node] = payload.Value
        else:
            raise Exception(f"Scada not tracking SimpleSensor readings from {from_node}!")

    def gt_driver_booleanactuator_cmd_record_received(
        self, from_node: ShNode, payload: GtDriverBooleanactuatorCmd
    ):
        if from_node.alias != payload.ShNodeAlias:
            raise Exception("Command record must come from the boolean actuator actor")
        self.recent_ba_cmds[from_node].append(payload.RelayState)
        self.recent_ba_cmd_times_unix_ms[from_node].append(payload.CommandTimeUnixMs)

    def gw_subscriptions(self) -> List[Subscription]:
        return [
            Subscription(
                Topic=f"{settings.ATN_G_NODE_ALIAS}/{GtDispatch_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
            Subscription(
                Topic=f"{settings.ATN_G_NODE_ALIAS}/{GtShCliAtnCmd_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
        ]

    def on_gw_message(self, payload) -> ScadaCmdDiagnostic:
        from_node = ShNode.by_alias["a"]

        if isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
            return ScadaCmdDiagnostic.SUCCESS
        elif isinstance(payload, GtDispatch):
            self.gt_dispatch_received(from_node, payload)
            return ScadaCmdDiagnostic.SUCCESS
        elif isinstance(payload, GtShCliAtnCmd):
            self.gt_sh_cli_atn_cmd_received(payload)
            return ScadaCmdDiagnostic.SUCCESS
        else:
            self.screen_print(f"{payload} subscription not implemented!")
            return ScadaCmdDiagnostic.PAYLOAD_NOT_IMPLEMENTED

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
        else:
            self.turn_off(ba)

    def make_status_snapshot(self) -> GtShStatusSnapshot:
        about_node_alias_list = []
        value_list = []
        telemetry_name_list = []
        for node in self.my_simple_sensors():
            if self.latest_simple_value[node] is not None:
                about_node_alias_list.append(node.alias)
                value_list.append(self.latest_simple_value[node])
                telemetry_name_list.append(self.config[node].reporting.TelemetryName)
        for tt in self.my_telemetry_tuples():
            if self.latest_value_from_multipurpose_sensor[tt] is not None:
                about_node_alias_list.append(tt.AboutNode.alias)
                value_list.append(self.latest_value_from_multipurpose_sensor[tt])
                telemetry_name_list.append(tt.TelemetryName)
        return GtShStatusSnapshot_Maker(
            about_node_alias_list=about_node_alias_list,
            report_time_unix_ms=int(1000 * time.time()),
            value_list=value_list,
            telemetry_name_list=telemetry_name_list,
        ).tuple

    def gt_sh_cli_atn_cmd_received(self, payload: GtShCliAtnCmd):
        if payload.SendSnapshot is not True:
            return

        snapshot = self.make_status_snapshot()
        payload = GtShCliScadaResponse_Maker(snapshot=snapshot).tuple
        self.gw_publish(payload=payload)

    ################################################
    # Primary functions
    ###############################################

    def turn_on(self, ba: ShNode) -> ScadaCmdDiagnostic:
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        dispatch_payload = GtDispatch_Maker(
            relay_state=1, sh_node_alias=ba.alias, send_time_unix_ms=int(time.time() * 1000)
        ).tuple
        self.publish(payload=dispatch_payload)
        self.gw_publish(payload=dispatch_payload)
        self.screen_print(f"Dispatched {ba.alias}  on")
        return ScadaCmdDiagnostic.SUCCESS

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        dispatch_payload = GtDispatch_Maker(
            relay_state=0, sh_node_alias=ba.alias, send_time_unix_ms=int(time.time() * 1000)
        ).tuple
        self.publish(payload=dispatch_payload)
        self.gw_publish(payload=dispatch_payload)
        self.screen_print(f"Dispatched {ba.alias} off")
        return ScadaCmdDiagnostic.SUCCESS

    def make_simple_telemetry_status(self, node: ShNode) -> Optional[GtShSimpleTelemetryStatus]:
        if node in self.my_simple_sensors():
            if len(self.recent_simple_values[node]) == 0:
                return None
            read_time_unix_ms_list = self.recent_simple_read_times_unix_ms[node]
            value_list = self.recent_simple_values[node]
            telemetry_name = self.config[node].reporting.TelemetryName
            return GtShSimpleTelemetryStatus_Maker(
                sh_node_alias=node.alias,
                telemetry_name=telemetry_name,
                value_list=value_list,
                read_time_unix_ms_list=read_time_unix_ms_list,
            ).tuple
        else:
            return None

    def make_multipurpose_telemetry_status(
        self, tt: TelemetryTuple
    ) -> Optional[GtShMultipurposeTelemetryStatus]:
        if tt in self.my_telemetry_tuples():
            if len(self.recent_values_from_multipurpose_sensor[tt]) == 0:
                return None
            read_time_unix_ms_list = self.recent_read_times_unix_ms_from_multipurpose_sensor[tt]
            value_list = self.recent_values_from_multipurpose_sensor[tt]
            return GtShMultipurposeTelemetryStatus_Maker(
                about_node_alias=tt.AboutNode.alias,
                sensor_node_alias=tt.SensorNode.alias,
                telemetry_name=tt.TelemetryName,
                value_list=value_list,
                read_time_unix_ms_list=read_time_unix_ms_list,
            ).tuple
        else:
            return None

    def make_booleanactuator_cmd_status(
        self, node: ShNode
    ) -> Optional[GtShBooleanactuatorCmdStatus]:
        if node not in self.my_boolean_actuators():
            return None
        if len(self.recent_ba_cmds[node]) == 0:
            return None
        return GtShBooleanactuatorCmdStatus_Maker(
            sh_node_alias=node.alias,
            relay_state_command_list=self.recent_ba_cmds[node],
            command_time_unix_ms_list=self.recent_ba_cmd_times_unix_ms[node],
        ).tuple

    def send_status(self):
        self.screen_print("Should send status")
        simple_telemetry_list = []
        multipurpose_telemetry_list = []
        booleanactuator_cmd_list = []
        for node in self.my_simple_sensors():
            status = self.make_simple_telemetry_status(node)
            if status:
                simple_telemetry_list.append(status)
        for tt in self.my_telemetry_tuples():
            status = self.make_multipurpose_telemetry_status(tt)
            if status:
                multipurpose_telemetry_list.append(status)
        for node in self.my_boolean_actuators():
            status = self.make_booleanactuator_cmd_status(node)
            if status:
                booleanactuator_cmd_list.append(status)

        slot_start_unix_s = self._last_5_cron_s
        payload = GtShStatus_Maker(
            about_g_node_alias=helpers.ta_g_node_alias(),
            slot_start_unix_s=slot_start_unix_s,
            reporting_period_s=settings.SCADA_REPORTING_PERIOD_S,
            booleanactuator_cmd_list=booleanactuator_cmd_list,
            multipurpose_telemetry_list=multipurpose_telemetry_list,
            simple_telemetry_list=simple_telemetry_list,
        ).tuple
        self.payload = payload
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
            responsive_sleep(self, 1)
            if int(time.time()) % 30 == 0:
                self.screen_print(f"{pendulum.from_timestamp(int(time.time()))}")
                self.screen_print(f"{self.next_5_cron_s - int(time.time())} seconds till status")

    @property
    def next_5_cron_s(self) -> int:
        last_cron_s = self._last_5_cron_s - (self._last_5_cron_s % 300)
        return last_cron_s + 300

    def time_for_5_cron(self) -> bool:
        if time.time() > self.next_5_cron_s:
            return True
        return False
