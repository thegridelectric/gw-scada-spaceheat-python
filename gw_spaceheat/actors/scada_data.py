"""Container for data Scada uses in building status and snapshot messages, separated from Scada for clarity,
not necessarily re-use. """

import time
import uuid
from typing import Dict
from typing import List
from typing import Optional

from gwproto.messages import GtShMultipurposeTelemetryStatus
from gwproto.messages import GtShStatus
from gwproto.messages import SnapshotSpaceheat
from gwproto.messages import TelemetrySnapshotSpaceheat

from actors.config import ScadaSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.telemetry_tuple import TelemetryTuple


class ScadaData:
    latest_total_power_w: Optional[int]
    status_to_store: Dict[str, GtShStatus]
    latest_value_from_multipurpose_sensor: Dict[TelemetryTuple, int]
    recent_values_from_multipurpose_sensor: Dict[TelemetryTuple, List]
    recent_read_times_unix_ms_from_multipurpose_sensor: Dict[TelemetryTuple, List]
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

        self.latest_value_from_multipurpose_sensor: Dict[TelemetryTuple, int] = {  # noqa
            tt: None for tt in hardware_layout.my_telemetry_tuples
        }
        self.recent_values_from_multipurpose_sensor: Dict[TelemetryTuple, List] = {
            tt: [] for tt in hardware_layout.my_telemetry_tuples
        }
        self.recent_read_times_unix_ms_from_multipurpose_sensor: Dict[
            TelemetryTuple, List
        ] = {tt: [] for tt in hardware_layout.my_telemetry_tuples}

        self.flush_latest_readings()

    def flush_latest_readings(self):
        self.recent_values_from_multipurpose_sensor = {
            tt: [] for tt in self.hardware_layout.my_telemetry_tuples
        }
        self.recent_read_times_unix_ms_from_multipurpose_sensor = {
            tt: [] for tt in self.hardware_layout.my_telemetry_tuples
        }

    def make_multipurpose_telemetry_status(
        self, tt: TelemetryTuple
    ) -> Optional[GtShMultipurposeTelemetryStatus]:
        if tt in self.hardware_layout.my_telemetry_tuples:
            if len(self.recent_values_from_multipurpose_sensor[tt]) == 0:
                return None
            return GtShMultipurposeTelemetryStatus(
                AboutNodeAlias=tt.AboutNode.alias,
                SensorNodeAlias=tt.SensorNode.alias,
                TelemetryName=tt.TelemetryName,
                ValueList=self.recent_values_from_multipurpose_sensor[tt],
                ReadTimeUnixMsList=self.recent_read_times_unix_ms_from_multipurpose_sensor[tt],
            )
        else:
            return None

    def make_status(self, slot_start_seconds: int) -> GtShStatus:
        simple_telemetry_list = []
        multipurpose_telemetry_list = []
        booleanactuator_cmd_list = []
        for tt in self.hardware_layout.my_telemetry_tuples:
            status = self.make_multipurpose_telemetry_status(tt)
            if status:
                multipurpose_telemetry_list.append(status)
        return GtShStatus(
            FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
            FromGNodeId=self.hardware_layout.scada_g_node_id,
            StatusUid=str(uuid.uuid4()),
            AboutGNodeAlias=self.hardware_layout.terminal_asset_g_node_alias,
            SlotStartUnixS=slot_start_seconds,
            ReportingPeriodS=self.settings.seconds_per_report,
            BooleanactuatorCmdList=booleanactuator_cmd_list,
            MultipurposeTelemetryList=multipurpose_telemetry_list,
            SimpleTelemetryList=simple_telemetry_list,
        )

    def make_telemetry_snapshot(self) -> TelemetrySnapshotSpaceheat:
        about_node_alias_list = []
        value_list = []
        telemetry_name_list = []
        for tt in self.hardware_layout.my_telemetry_tuples:
            if self.latest_value_from_multipurpose_sensor[tt] is not None:
                about_node_alias_list.append(tt.AboutNode.alias)
                value_list.append(self.latest_value_from_multipurpose_sensor[tt])
                telemetry_name_list.append(tt.TelemetryName)
        return TelemetrySnapshotSpaceheat(
            AboutNodeAliasList=about_node_alias_list,
            ReportTimeUnixMs=int(1000 * time.time()),
            ValueList=value_list,
            TelemetryNameList=telemetry_name_list,
        )

    def make_snapshot(self) -> SnapshotSpaceheat:
        return SnapshotSpaceheat(
            FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
            FromGNodeInstanceId=self.hardware_layout.scada_g_node_id,
            Snapshot=self.make_telemetry_snapshot(),
        )

    def make_snaphsot_payload(self) -> dict:
        return self.make_snapshot().model_dump()
