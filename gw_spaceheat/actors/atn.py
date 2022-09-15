import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from actors.cloud_base import CloudBase
from actors.utils import QOS, Subscription, responsive_sleep
from config import ScadaSettings, Paths
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_dispatch_boolean.gt_dispatch_boolean_maker import GtDispatchBoolean_Maker
from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd_maker import GtShCliAtnCmd_Maker
from schema.gt.snapshot_spaceheat.snapshot_spaceheat_maker import (
    SnapshotSpaceheat,
    SnapshotSpaceheat_Maker,
)

from schema.gt.gt_sh_status.gt_sh_status_maker import GtShStatus, GtShStatus_Maker


class Atn(CloudBase):

    def my_sensors(self) -> List[ShNode]:
        all_nodes = list(self.nodes.nodes.values())
        return list(
            filter(
                lambda x: (
                    x.role == Role.TANK_WATER_TEMP_SENSOR
                    or x.role == Role.BOOLEAN_ACTUATOR
                    or x.role == Role.PIPE_TEMP_SENSOR
                    or x.role == Role.PIPE_FLOW_METER
                    or x.role == Role.POWER_METER
                ),
                all_nodes,
            )
        )

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        super(Atn, self).__init__(settings=settings, hardware_layout=hardware_layout)
        self.node = hardware_layout.node(alias)
        self.latest_power_w: Dict[ShNode, Optional[int]] = {}
        self.power_nodes = list(
            filter(
                lambda x: x.role == Role.BOOST_ELEMENT and x.has_actor,
                self.nodes.nodes.values()
            )
        )
        for node in self.power_nodes:
            self.latest_power_w[node] = None
        self.latest_status: Optional[GtShStatus] = None
        self.status_output_dir = self.settings.paths.data_dir / "status"
        self.status_output_dir.mkdir(parents=True, exist_ok=True)
        self.log_csv = str(self.settings.paths.log_dir / f"atn_{str(uuid.uuid4()).split('-')[1]}.csv")
        self.total_power_w = 0
        self.screen_print(f"Initialized {self.__class__}")

    def gw_subscriptions(self) -> List[Subscription]:
        return [
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{GsPwr_Maker.type_alias}",
                Qos=QOS.AtMostOnce,
            ),
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{GtShStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
            Subscription(
                Topic=f"{self.scada_g_node_alias}/{SnapshotSpaceheat_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
        ]

    def on_gw_message(self, from_node: ShNode, payload):
        if from_node != self.nodes.node("a.s"):
            raise Exception("gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(payload)
        elif isinstance(payload, SnapshotSpaceheat):
            self.gt_sh_cli_scada_response_received(payload)
        elif isinstance(payload, GtShStatus):
            self.gt_sh_status_received(payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, payload: GsPwr):
        self.latest_power_w = payload.Power
        self.total_power_w = self.latest_power_w

    def gt_sh_status_received(self, payload: GtShStatus):
        self.latest_status = payload
        status_file = self.status_output_dir / f"GtShStatus.{payload.SlotStartUnixS}.json"
        with status_file.open("w") as f:
            f.write(payload.as_type())
        print(f"Wrote status file [{status_file}]")

    def gt_sh_cli_scada_response_received(self, payload: SnapshotSpaceheat):
        snapshot = payload.Snapshot
        for node in self.my_sensors():
            if node.alias not in snapshot.AboutNodeAliasList:
                self.screen_print(f"No data for {node.alias}")

        for i in range(len(snapshot.AboutNodeAliasList)):
            print(
                f"{snapshot.AboutNodeAliasList[i]}: {snapshot.ValueList[i]} {snapshot.TelemetryNameList[i].value}"
            )

    ################################################
    # Primary functions
    ################################################

    def status(self):
        payload = GtShCliAtnCmd_Maker(
            from_g_node_alias=self.atn_g_node_alias,
            from_g_node_id=self.atn_g_node_id,
            send_snapshot=True,
        ).tuple
        self.gw_publish(payload)

    def turn_on(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        payload = GtDispatchBoolean_Maker(
            to_g_node_alias=self.scada_g_node_alias,
            from_g_node_alias=self.atn_g_node_alias,
            from_g_node_id=self.atn_g_node_id,
            about_node_alias=ba.alias,
            relay_state=1,
            send_time_unix_ms=int(time.time() * 1000),
        ).tuple
        self.gw_publish(payload)

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        payload = GtDispatchBoolean_Maker(
            to_g_node_alias=self.scada_g_node_alias,
            from_g_node_alias=self.atn_g_node_alias,
            from_g_node_id=self.atn_g_node_id,
            about_node_alias=ba.alias,
            relay_state=0,
            send_time_unix_ms=int(time.time() * 1000),
        ).tuple
        self.gw_publish(payload)

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            responsive_sleep(self, 1)

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
