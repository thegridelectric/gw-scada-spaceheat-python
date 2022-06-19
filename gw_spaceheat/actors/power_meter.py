
import random
import time
from typing import List

from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr_Maker

from actors.actor_base import ActorBase
from actors.utils import Subscription


class PowerMeter(ActorBase):
    def __init__(self, node: ShNode, logging_on=False):
        super(PowerMeter, self).__init__(node=node, logging_on=logging_on)
        self.total_power_w = 4230
        self.screen_print(f'Initialized {self.__class__}')

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, from_node: ShNode, payload):
        pass

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            self.total_power_w += 250 - int(500 * random.random())
            payload = GsPwr_Maker(power=self.total_power_w).tuple
            self.publish(payload=payload)
            time.sleep(1)
