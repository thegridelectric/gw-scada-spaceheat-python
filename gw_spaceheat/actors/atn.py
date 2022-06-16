
import time
from typing import List

import helpers
import settings
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_spaceheat_status.gt_spaceheat_status_maker import (
    GtSpaceheatStatus, GtSpaceheatStatus_Maker)

from actors.atn_base import AtnBase
from actors.utils import QOS, Subscription


class Atn(AtnBase):
    def __init__(self, node: ShNode):
        super(Atn, self).__init__(node=node)
        self.total_power_w = 0
        self.screen_print(f'Initialized {self.__class__}')

    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{helpers.scada_g_node_alias()}/{GsPwr_Maker.type_alias}', Qos=QOS.AtMostOnce),
                Subscription(Topic=f'{helpers.scada_g_node_alias()}/{GtSpaceheatStatus_Maker.type_alias}',
                             Qos=QOS.AtLeastOnce)]

    def on_gw_message(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias['a.s']:
            raise Exception("gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GtSpaceheatStatus):
            self.gt_spaceheat_status_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        self.total_power_w = payload.Power

    def gt_spaceheat_status_received(self, from_node: ShNode, payload: GtSpaceheatStatus):
        self.screen_print("Got status!")
        self.latest_status_payload = payload

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            time.sleep(1)
