from typing import List, Optional

import helpers
from data_classes.sh_node import ShNode
from schema.gt.gt_sh_status.gt_sh_status_maker import (
    GtShStatus,
    GtShStatus_Maker,
)

from actors.actor_base import ActorBase
from actors.utils import QOS, Subscription, responsive_sleep


class HomeAlone(ActorBase):
    MAIN_LOOP_MIN_TIME_S = 5

    def __init__(self, node: ShNode, logging_on=False):
        super(HomeAlone, self).__init__(node=node, logging_on=logging_on)
        self.latest_status: Optional[GtShStatus] = None
        self.screen_print(f"Initialized {self.__class__}")

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [
            Subscription(
                Topic=f"{helpers.scada_g_node_alias()}/{GtShStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            )
        ]
        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShStatus):
            self.gt_sh_simple_status_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gt_sh_simple_status_received(self, from_node: ShNode, payload: GtShStatus):
        self.screen_print("Got status!")
        if from_node != ShNode.by_alias["a.s"]:
            raise Exception(f"Got status from {from_node}! Expected a.s!")
        self.latest_status = payload

    ################################################
    # Primary functions
    ################################################

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            responsive_sleep(self, 1)
