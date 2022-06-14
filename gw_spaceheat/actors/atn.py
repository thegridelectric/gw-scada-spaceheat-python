
import threading
import time
from actors.atn_base import Atn_Base
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr import GsPwr


class Atn(Atn_Base):
    def __init__(self, node: ShNode):
        super(Atn, self).__init__(node=node)
        self.total_power_w = 0
        self.gw_consume()
        self.schedule_thread = threading.Thread(target=self.main)
        self.schedule_thread.start()
        self.screen_print(f'Started {self.__class__}')

    def on_gw_message(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias['a.s']:
            raise Exception(f"gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        self.total_power_w = payload.Power

    def terminate_scheduling(self):
        self._scheduler_running = False

    def main(self):
        self._scheduler_running = True
        while self._scheduler_running is True:
            # track time and send status every x minutes (likely 5)
            time.sleep(1)
