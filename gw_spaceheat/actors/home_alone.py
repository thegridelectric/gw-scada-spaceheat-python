import time
from typing import List

import helpers
from data_classes.sh_node import ShNode
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import (
    GtShSimpleStatus,
    GtShSimpleStatus_Maker,
)

from actors.actor_base import ActorBase
from actors.utils import QOS, Subscription


class HomeAlone(ActorBase):
    MAIN_LOOP_MIN_TIME_S = 5

    def __init__(self, node: ShNode, logging_on=False):
        super(HomeAlone, self).__init__(node=node, logging_on=logging_on)

        self.screen_print(f"Initialized {self.__class__}")

    def subscriptions(self) -> List[Subscription]:
        my_subscriptions = [
            Subscription(
                Topic=f"{helpers.scada_g_node_alias()}/{GtShSimpleStatus_Maker.type_alias}",
                Qos=QOS.AtLeastOnce,
            )
        ]
        return my_subscriptions

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShSimpleStatus):
            self.gt_sh_simple_status_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gt_sh_simple_status_received(
        self, from_node: ShNode, payload: GtShSimpleStatus
    ):
        self.screen_print("Got status!")

    ################################################
    # Primary functions
    ################################################

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            time.sleep(1)
