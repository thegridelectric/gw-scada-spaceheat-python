
import time

from data_classes.sh_node import ShNode
from schema.gs.gs_pwr import GsPwr

from actors.atn_base import Atn_Base


class Atn(Atn_Base):
    def __init__(self, node: ShNode):
        super(Atn, self).__init__(node=node)
        self.total_power_w = 0
        self.screen_print(f'Initialized {self.__class__}')

    def on_gw_message(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias['a.s']:
            raise Exception("gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        self.total_power_w = payload.Power

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            time.sleep(1)
