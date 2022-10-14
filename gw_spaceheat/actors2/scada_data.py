"""Container for data Scada uses in building status and snapshot messages, separated from Scada2 for clarity,
not necessarily re-use. """

import time
import uuid
from typing import Dict
from typing import List
from typing import Optional

from config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.node_config import NodeConfig
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums import TelemetryName
from schema.messages import GtShBooleanactuatorCmdStatus
from schema.messages import GtShBooleanactuatorCmdStatus_Maker
from schema.messages import GtShMultipurposeTelemetryStatus
from schema.messages import GtShMultipurposeTelemetryStatus_Maker
from schema.messages import GtShSimpleTelemetryStatus
from schema.messages import GtShSimpleTelemetryStatus_Maker
from schema.messages import GtShStatus
from schema.messages import GtShStatus_Maker
from schema.messages import SnapshotSpaceheat
from schema.messages import SnapshotSpaceheat_Maker
from schema.messages import TelemetrySnapshotSpaceheat
from schema.messages import TelemetrySnapshotSpaceheat_Maker


class ScadaData:
    latest_total_power_w: Optional[int]
    status_to_store: Dict[str, GtShStatus]
    latest_simple_value: Dict[ShNode, int]
    recent_simple_values: Dict[ShNode, List]
    recent_simple_read_times_unix_ms: Dict[ShNode, List]
    latest_value_from_multipurpose_sensor: Dict[TelemetryTuple, int]
    recent_values_from_multipurpose_sensor: Dict[TelemetryTuple, List]
    recent_read_times_unix_ms_from_multipurpose_sensor: Dict[TelemetryTuple, List]
    recent_ba_cmds: Dict[ShNode, List]
    recent_ba_cmd_times_unix_ms: Dict[ShNode, List]
    telemetry_names: Dict[ShNode, TelemetryName]
    settings: ScadaSettings
    hardware_layout: HardwareLayout

    def __init__(self, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self.latest_total_power_w: Optional[int] = None

        # status_to_store is a placeholder Dict of GtShStatus
        # objects by StatusUid key that we want to store
        # (probably about 3 weeks worth) and access on restart
        self.latest_total_power_w: Optional[int] = None
        self.status_to_store: Dict[str:GtShStatus] = {}

        self.settings = settings
        self.hardware_layout = hardware_layout
        self.telemetry_names = {
            node: NodeConfig(node, self.settings).reporting.TelemetryName
            for node in hardware_layout.my_simple_sensors
        }

        self.latest_simple_value: Dict[ShNode, int] = {
            node: None for node in hardware_layout.my_simple_sensors
        }
        self.recent_simple_values: Dict[ShNode, List] = {
            node: [] for node in hardware_layout.my_simple_sensors
        }
        self.recent_simple_read_times_unix_ms: Dict[ShNode, List] = {
            node: [] for node in hardware_layout.my_simple_sensors
        }

        self.latest_value_from_multipurpose_sensor: Dict[TelemetryTuple, int] = {
            tt: None for tt in hardware_layout.my_telemetry_tuples
        }
        self.recent_values_from_multipurpose_sensor: Dict[TelemetryTuple, List] = {
            tt: [] for tt in hardware_layout.my_telemetry_tuples
        }
        self.recent_read_times_unix_ms_from_multipurpose_sensor: Dict[
            TelemetryTuple, List
        ] = {tt: [] for tt in hardware_layout.my_telemetry_tuples}
        self.recent_ba_cmds: Dict[ShNode, List] = {
            node: [] for node in hardware_layout.my_boolean_actuators
        }

        self.recent_ba_cmd_times_unix_ms: Dict[ShNode, List] = {
            node: [] for node in hardware_layout.my_boolean_actuators
        }

        self.flush_latest_readings()

    def flush_latest_readings(self):
        self.recent_simple_values = {node: [] for node in self.hardware_layout.my_simple_sensors}
        self.recent_simple_read_times_unix_ms = {
            node: [] for node in self.hardware_layout.my_simple_sensors
        }

        self.recent_values_from_multipurpose_sensor = {
            tt: [] for tt in self.hardware_layout.my_telemetry_tuples
        }
        self.recent_read_times_unix_ms_from_multipurpose_sensor = {
            tt: [] for tt in self.hardware_layout.my_telemetry_tuples
        }

        self.recent_ba_cmds = {node: [] for node in self.hardware_layout.my_boolean_actuators}
        self.recent_ba_cmd_times_unix_ms = {
            node: [] for node in self.hardware_layout.my_boolean_actuators
        }

    def make_simple_telemetry_status(
        self, node: ShNode
    ) -> Optional[GtShSimpleTelemetryStatus]:
        if node in self.hardware_layout.my_simple_sensors:
            if len(self.recent_simple_values[node]) == 0:
                return None
            read_time_unix_ms_list = self.recent_simple_read_times_unix_ms[node]
            value_list = self.recent_simple_values[node]
            telemetry_name = self.telemetry_names[node]
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
        if tt in self.hardware_layout.my_telemetry_tuples:
            if len(self.recent_values_from_multipurpose_sensor[tt]) == 0:
                return None
            read_time_unix_ms_list = (
                self.recent_read_times_unix_ms_from_multipurpose_sensor[tt]
            )
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
        if node not in self.hardware_layout.my_boolean_actuators:
            return None
        if len(self.recent_ba_cmds[node]) == 0:
            return None
        return GtShBooleanactuatorCmdStatus_Maker(
            sh_node_alias=node.alias,
            relay_state_command_list=self.recent_ba_cmds[node],
            command_time_unix_ms_list=self.recent_ba_cmd_times_unix_ms[node],
        ).tuple

    def make_status(self, slot_start_seconds: int) -> GtShStatus:
        simple_telemetry_list = []
        multipurpose_telemetry_list = []
        booleanactuator_cmd_list = []
        for node in self.hardware_layout.my_simple_sensors:
            status = self.make_simple_telemetry_status(node)
            if status:
                simple_telemetry_list.append(status)
        for tt in self.hardware_layout.my_telemetry_tuples:
            status = self.make_multipurpose_telemetry_status(tt)
            if status:
                multipurpose_telemetry_list.append(status)
        for node in self.hardware_layout.my_boolean_actuators:
            status = self.make_booleanactuator_cmd_status(node)
            if status:
                booleanactuator_cmd_list.append(status)
        return GtShStatus_Maker(
            from_g_node_alias=self.hardware_layout.scada_g_node_alias,
            from_g_node_id=self.hardware_layout.scada_g_node_id,
            status_uid=str(uuid.uuid4()),
            about_g_node_alias=self.hardware_layout.terminal_asset_g_node_alias,
            slot_start_unix_s=slot_start_seconds,
            reporting_period_s=self.settings.seconds_per_report,
            booleanactuator_cmd_list=booleanactuator_cmd_list,
            multipurpose_telemetry_list=multipurpose_telemetry_list,
            simple_telemetry_list=simple_telemetry_list,
        ).tuple

    def make_telemetry_snapshot(self) -> TelemetrySnapshotSpaceheat:
        about_node_alias_list = []
        value_list = []
        telemetry_name_list = []
        for node in self.hardware_layout.my_simple_sensors:
            if self.latest_simple_value[node] is not None:
                about_node_alias_list.append(node.alias)
                value_list.append(self.latest_simple_value[node])
                telemetry_name_list.append(self.telemetry_names[node])
        for tt in self.hardware_layout.my_telemetry_tuples:
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
            from_g_node_alias=self.hardware_layout.scada_g_node_alias,
            from_g_node_instance_id=self.hardware_layout.scada_g_node_id,
            snapshot=self.make_telemetry_snapshot(),
        ).tuple

    def make_snaphsot_payload(self) -> dict:
        return self.make_snapshot().asdict()
