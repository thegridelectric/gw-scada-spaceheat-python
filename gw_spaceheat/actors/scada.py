import enum
import time
import uuid
from typing import Dict
from typing import List
from typing import Optional

from gwproto.messages import GsPwr
from gwproto.messages import GsPwr_Maker
from gwproto.messages import GtDispatchBoolean
from gwproto.messages import GtDispatchBoolean_Maker
from gwproto.messages import GtDispatchBooleanLocal
from gwproto.messages import GtDispatchBooleanLocal_Maker
from gwproto.messages import GtDriverBooleanactuatorCmd
from gwproto.messages import GtDriverBooleanactuatorCmd_Maker
from gwproto.messages import GtShBooleanactuatorCmdStatus
from gwproto.messages import GtShBooleanactuatorCmdStatus_Maker
from gwproto.messages import GtShCliAtnCmd
from gwproto.messages import GtShCliAtnCmd_Maker
from gwproto.messages import GtShMultipurposeTelemetryStatus
from gwproto.messages import GtShMultipurposeTelemetryStatus_Maker
from gwproto.messages import GtShSimpleTelemetryStatus
from gwproto.messages import GtShSimpleTelemetryStatus_Maker
from gwproto.messages import GtShStatus
from gwproto.messages import GtShStatus_Maker
from gwproto.messages import GtShTelemetryFromMultipurposeSensor
from gwproto.messages import GtShTelemetryFromMultipurposeSensor_Maker
from gwproto.messages import GtTelemetry
from gwproto.messages import GtTelemetry_Maker
from gwproto.messages import SnapshotSpaceheat
from gwproto.messages import SnapshotSpaceheat_Maker
from gwproto.messages import TelemetrySnapshotSpaceheat
from gwproto.messages import TelemetrySnapshotSpaceheat_Maker

from actors.scada_base import ScadaBase
from actors.utils import QOS
from actors.utils import Subscription
from actors.utils import responsive_sleep
from actors2.config import ScadaSettings
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.node_config import NodeConfig
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums import Role


class ScadaCmdDiagnostic(enum.Enum):
    SUCCESS = "Success"
    PAYLOAD_NOT_IMPLEMENTED = "PayloadNotImplemented"
    BAD_FROM_NODE = "BadFromNode"
    DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR = "DispatchNodeNotBooleanActuator"
    UNKNOWN_DISPATCH_NODE = "UnknownDispatchNode"
    IGNORING_HOMEALONE_DISPATCH = "IgnoringHomealoneDispatch"
    IGNORING_ATN_DISPATCH = "IgnoringAtnDispatch"


class Scada(ScadaBase):
    GS_PWR_MULTIPLIER = 1
    ASYNC_POWER_REPORT_THRESHOLD = 0.05

    def my_home_alone(self) -> ShNode:
        all_nodes = list(self.layout.nodes.values())
        home_alone_nodes = list(filter(lambda x: (x.role == Role.HOME_ALONE), all_nodes))
        if len(home_alone_nodes) != 1:
            raise Exception("there should be a single SpaceheatNode with role HomeAlone")
        return home_alone_nodes[0]

    def my_boolean_actuators(self) -> List[ShNode]:
        all_nodes = list(self.layout.nodes.values())
        return list(filter(lambda x: (x.role == Role.BOOLEAN_ACTUATOR), all_nodes))

    def my_simple_sensors(self) -> List[ShNode]:
        all_nodes = list(self.layout.nodes.values())
        return list(
            filter(
                lambda x: (
                    x.role == Role.TANK_WATER_TEMP_SENSOR
                    or x.role == Role.BOOLEAN_ACTUATOR
                    or x.role == Role.PIPE_TEMP_SENSOR
                    or x.role == Role.PIPE_FLOW_METER
                    or x.role == Role.ROOM_TEMP_SENSOR
                ),
                all_nodes,
            )
        )

    def my_multipurpose_sensors(self) -> List[ShNode]:
        """This will be a list of all sensing devices that either measure more
        than one ShNode or measure more than one physical quantity type (or both).
        This includes the (unique) power meter, but may also include other roles like thermostats
        and heat pumps."""
        all_nodes = list(self.layout.nodes.values())
        return list(filter(lambda x: (x.role == Role.POWER_METER), all_nodes))

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        super(Scada, self).__init__(alias=alias, settings=settings, hardware_layout=hardware_layout)
        if self.node != self.scada_node():
            raise Exception(f"The node for Scada must be {self.scada_node()}, not {self.node}!")
        # hack before dispatch contract is implemented
        self._scada_atn_fast_dispatch_contract_is_alive_stub = False

        now = int(time.time())
        self._last_5_cron_s = now - (now % 300)

        # status_to_store is a placeholder Dict of GtShStatus
        # objects by StatusUid key that we want to store
        # (probably about 3 weeks worth) and access on restart
        self.latest_total_power_w: Optional[int] = None
        self.status_to_store: Dict[str:GtShStatus] = {}

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

    @property
    def scada_atn_fast_dispatch_contract_is_alive(self):
        """
        TO IMPLEMENT:

         False if:
           - no contract exists
           - interactive polling between atn and scada is down
           - scada sent dispatch command with more than 6 seconds before response
             as measured by power meter (requires a lot of clarification)
           - average time for response to dispatch commands in last 50 dispatches
             exceeds 3 seconds
           - Scada has not sent in daily attestion that power metering is
             working and accurate
           - Scada requests local control and Atn has agreed
           - Atn requests that Scada take local control and Scada has agreed
           - Scada has not sent in an attestion that metering is good in the
             previous 24 hours

           Otherwise true

           Note that typically, the contract will not be alive because of house to
           cloud comms failure. But not always. There will be significant and important
           times (like when testing home alone perforamance) where we will want to send
           status messages etc up to the cloud even when the dispatch contract is not
           alive.
        """
        return self._scada_atn_fast_dispatch_contract_is_alive_stub

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
            self.config[node] = NodeConfig(node, self.settings)

    def my_telemetry_tuples(self) -> List[TelemetryTuple]:
        """This will include telemetry tuples from all the multipurpose sensors, the most
        important of which is the power meter."""
        return self.all_power_meter_telemetry_tuples()

    ################################################
    # Receiving messages
    ###############################################

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [Subscription(Topic=f"a.m/{GsPwr_Maker.type_alias}", Qos=QOS.AtMostOnce)]

        my_subscriptions.append(
            Subscription(
                Topic=f"{self.my_home_alone().alias}/{GtDispatchBooleanLocal_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            )
        )

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
            if from_node is self.power_meter_node():
                self.gs_pwr_received(from_node, payload)
            else:
                raise Exception(
                    f"from_node {from_node} must be from {self.power_meter_node()} for GsPwr message"
                )
        elif isinstance(payload, GtDispatchBooleanLocal):
            if from_node == self.layout.node("a.home"):
                self.local_boolean_dispatch_received(from_node, payload)
            else:
                raise Exception("from_node must be a.home for GsDispatchBooleanLocal message")
        elif isinstance(payload, GtTelemetry):
            if from_node in self.my_simple_sensors():
                self.gt_telemetry_received(from_node, payload),
        elif isinstance(payload, GtShTelemetryFromMultipurposeSensor):
            if from_node in self.my_multipurpose_sensors():
                self.gt_sh_telemetry_from_multipurpose_sensor_received(from_node, payload)
        elif isinstance(payload, GtDriverBooleanactuatorCmd):
            if from_node in self.my_boolean_actuators():
                self.gt_driver_booleanactuator_cmd_record_received(from_node, payload)
        else:
            raise Exception(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        """The highest priority of the SCADA, from the perspective of the electric grid,
        is to report power changes as quickly as possible (i.e. milliseconds matter) on
        any asynchronous change more than x% (probably 2%).

        There is a single meter measuring all power getting reported - this is in fact
        what is Atomic (i.e. cannot be divided further) about the AtomicTNode. The
        asynchronous change calculation is already made in the power meter code. This
        function just passes through the result.

        The allocation to separate metered nodes is done ex-poste using the multipurpose
        telemetry data."""

        self.gw_publish(payload)
        self.latest_total_power_w = self.GS_PWR_MULTIPLIER * payload.Power

    def gt_sh_telemetry_from_multipurpose_sensor_received(
        self, from_node: ShNode, payload: GtShTelemetryFromMultipurposeSensor
    ):
        if from_node in self.my_multipurpose_sensors():
            about_node_alias_list = payload.AboutNodeAliasList
            for idx, about_alias in enumerate(about_node_alias_list):
                if about_alias not in self.layout.nodes:
                    raise Exception(
                        f"alias {about_alias} in payload.AboutNodeAliasList not a recognized ShNode!"
                    )
                tt = TelemetryTuple(
                    AboutNode=self.layout.node(about_alias),
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
        """The boolean actuator actor reports when it has sent an actuation command
        to its driver. We add this to information to be sent up in the 5 minute status
        package.

        This is different than reporting a _reading_ of the state of the
        actuator. Note that a reading of the state of the actuator may not mean the relay
        is in the read position. For example, the NCD relay requires two power sources - one
        from the Pi and one a lowish DC voltage from another plug (12 or 24V). If the second
        power source is off, the relay will still report being on when it is actually off.

        Note also that the thing getting actuated (for example the boost element in the water
        tank) may not be getting any power because of another relay in series. For example, we
        can throw a large 240V breaker in the test garage and the NCD relay will actuate without
        the boost element turning on. Or the element could be burned out.

        So measuring the current and/or power of the thing getting
        actuated is really the best test."""

        if from_node not in self.my_boolean_actuators():
            raise Exception("boolean actuator command records must come from boolean actuator")
        if from_node.alias != payload.ShNodeAlias:
            raise Exception("Command record must come from the boolean actuator actor")
        self.recent_ba_cmds[from_node].append(payload.RelayState)
        self.recent_ba_cmd_times_unix_ms[from_node].append(payload.CommandTimeUnixMs)

    def gw_subscriptions(self) -> List[Subscription]:
        return [
            Subscription(
                Topic=f"{self.atn_g_node_alias}/{GtDispatchBoolean_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
            Subscription(
                Topic=f"{self.atn_g_node_alias}/{GtShCliAtnCmd_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
        ]

    def on_gw_message(self, payload) -> ScadaCmdDiagnostic:
        if isinstance(payload, GtDispatchBoolean):
            self.boolean_dispatch_received(payload)
            return ScadaCmdDiagnostic.SUCCESS
        elif isinstance(payload, GtShCliAtnCmd):
            self.gt_sh_cli_atn_cmd_received(payload)
            return ScadaCmdDiagnostic.SUCCESS
        else:
            self.screen_print(f"{payload} subscription not implemented!")
            return ScadaCmdDiagnostic.PAYLOAD_NOT_IMPLEMENTED

    def process_boolean_dispatch(self, payload: GtDispatchBoolean) -> ScadaCmdDiagnostic:
        if payload.AboutNodeAlias not in self.layout.nodes.keys():
            self.screen_print(f"dispatch received for unknown sh_node {payload.AboutNodeAlias}")
            return ScadaCmdDiagnostic.UNKNOWN_DISPATCH_NODE
        ba = self.layout.node(payload.AboutNodeAlias)
        if not isinstance(ba.component, BooleanActuatorComponent):
            self.screen_print(f"{ba} must be a BooleanActuator!")
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        if payload.RelayState == 1:
            self.turn_on(ba)
        else:
            self.turn_off(ba)
        return ScadaCmdDiagnostic.SUCCESS

    def local_boolean_dispatch_received(
        self, from_node: ShNode, payload: GtDispatchBooleanLocal
    ) -> ScadaCmdDiagnostic:
        """This will be a message from HomeAlone, honored when the DispatchContract
        with the Atn is not live."""
        if from_node != self.layout.node("a.home"):
            return ScadaCmdDiagnostic.BAD_FROM_NODE
        if self.scada_atn_fast_dispatch_contract_is_alive:
            return ScadaCmdDiagnostic.IGNORING_HOMEALONE_DISPATCH
        return self.process_boolean_dispatch(payload)

    def boolean_dispatch_received(self, payload: GtDispatchBoolean) -> ScadaCmdDiagnostic:
        """This is a dispatch message received from the atn. It is
        honored whenever DispatchContract with the Atn is live."""
        if not self.scada_atn_fast_dispatch_contract_is_alive:
            self.screen_print("Ignoring atn dispatch because DispatchContract not alive")
            return ScadaCmdDiagnostic.IGNORING_ATN_DISPATCH
        return self.process_boolean_dispatch(payload)

    def make_telemetry_snapshot(self) -> TelemetrySnapshotSpaceheat:
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
        return TelemetrySnapshotSpaceheat_Maker(
            about_node_alias_list=about_node_alias_list,
            report_time_unix_ms=int(1000 * time.time()),
            value_list=value_list,
            telemetry_name_list=telemetry_name_list,
        ).tuple

    def make_snapshot(self) -> SnapshotSpaceheat:
        return SnapshotSpaceheat_Maker(
            from_g_node_alias=self.scada_g_node_alias,
            from_g_node_instance_id=self.scada_g_node_id,
            snapshot=self.make_telemetry_snapshot(),
        ).tuple

    def gt_sh_cli_atn_cmd_received(self, payload: GtShCliAtnCmd):
        if payload.SendSnapshot is not True:
            return
        self.gw_publish(self.make_snapshot())

    ################################################
    # Primary functions
    ###############################################

    def turn_on(self, ba: ShNode) -> ScadaCmdDiagnostic:
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        dispatch_payload = GtDispatchBooleanLocal_Maker(
            from_node_alias=self.node.alias,
            about_node_alias=ba.alias,
            relay_state=1,
            send_time_unix_ms=int(time.time() * 1000),
        ).tuple
        self.publish(payload=dispatch_payload)
        self.screen_print(f"Dispatched {ba.alias}  on")
        return ScadaCmdDiagnostic.SUCCESS

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        dispatch_payload = GtDispatchBooleanLocal_Maker(
            from_node_alias=self.node.alias,
            about_node_alias=ba.alias,
            relay_state=0,
            send_time_unix_ms=int(time.time() * 1000),
        ).tuple
        self.publish(payload=dispatch_payload)
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

    def make_status(self) -> GtShStatus:
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
        return GtShStatus_Maker(
            from_g_node_alias=self.scada_g_node_alias,
            from_g_node_id=self.scada_g_node_id,
            status_uid=str(uuid.uuid4()),
            about_g_node_alias=self.terminal_asset_g_node_alias,
            slot_start_unix_s=slot_start_unix_s,
            reporting_period_s=self.settings.seconds_per_report,
            booleanactuator_cmd_list=booleanactuator_cmd_list,
            multipurpose_telemetry_list=multipurpose_telemetry_list,
            simple_telemetry_list=simple_telemetry_list,
        ).tuple

    def send_status(self):
        self.screen_print("Should send status")
        status = self.make_status()
        self.status_to_store[status.StatusUid] = status
        self.gw_publish(status)
        self.publish(status)
        self.gw_publish(self.make_snapshot())
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

    @property
    def next_5_cron_s(self) -> int:
        last_cron_s = self._last_5_cron_s - (self._last_5_cron_s % 300)
        return last_cron_s + 300

    def time_for_5_cron(self) -> bool:
        if time.time() > self.next_5_cron_s:
            return True
        return False
