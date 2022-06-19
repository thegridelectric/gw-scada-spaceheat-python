import time
import uuid
from typing import Dict, List, Optional

import helpers
import load_house
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_dispatch.gt_dispatch_maker import GtDispatch_Maker
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import (
    GtShSimpleStatus,
    GtShSimpleStatus_Maker,
)

from actors.cloud_base import CloudBase
from actors.utils import QOS, Subscription


class Atn(CloudBase):
    @classmethod
    def local_nodes(cls) -> List[ShNode]:
        load_house.load_all(input_json_file="input_data/houses.json")
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: (x.role != Role.ATN and x.has_actor), all_nodes))

    def __init__(self, node: ShNode, logging_on=False):
        super(Atn, self).__init__(logging_on=logging_on)
        self.node = node
        self.latest_power_w: Dict[ShNode, Optional[int]] = {}
        self.power_nodes = list(filter(lambda x: x.role == Role.BOOST_ELEMENT, self.local_nodes()))
        for node in self.power_nodes:
            self.latest_power_w[node] = None
        self.latest_status: Optional[GtShSimpleStatus] = None
        self.log_csv = f"output/debug_logs/atn_{str(uuid.uuid4()).split('-')[1]}.csv"
        self.total_power_w = 0
        self.screen_print(f"Initialized {self.__class__}")

    def gw_subscriptions(self) -> List[Subscription]:
        return [
            Subscription(
                Topic=f"{helpers.scada_g_node_alias()}/{GsPwr_Maker.type_alias}",
                Qos=QOS.AtMostOnce,
            ),
            Subscription(
                Topic=f"{helpers.scada_g_node_alias()}/{GtShSimpleStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            ),
        ]

    def on_gw_message(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias["a.s"]:
            raise Exception("gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(payload)
        elif isinstance(payload, GtShSimpleStatus):
            self.gt_sh_simple_status_received(payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, payload: GsPwr):
        self.latest_power_w = payload.Power
        self.total_power_w = self.latest_power_w

    def gt_sh_simple_status_received(self, payload: GtShSimpleStatus):
        self.latest_status = payload

    ################################################
    # Primary functions
    ################################################

    def turn_on(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        payload = GtDispatch_Maker(relay_state=1, sh_node_alias=ba.alias).tuple
        self.gw_publish(payload)

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        payload = GtDispatch_Maker(relay_state=0, sh_node_alias=ba.alias).tuple
        self.gw_publish(payload)

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            time.sleep(1)

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
