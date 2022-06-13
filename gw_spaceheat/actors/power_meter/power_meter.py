
import random
import time
import threading
from actors.power_meter.power_meter_base import PowerMeterBase
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr_Maker


class PowerMeter(PowerMeterBase):
    def __init__(self, node: ShNode):
        super(PowerMeter, self).__init__(node=node)
        self.total_power_w = 4230
        self.sensing_thread = threading.Thread(target=self.main)
        self.sensing_thread.start()
        self.screen_print(f'Started {self.__class__}')

    def terminate_sensing(self):
        self._sensing = False

    def main(self):
        self._sensing = True
        while self._sensing is True:
            self.total_power_w += 250 - int(500 * random.random())
            payload = GsPwr_Maker(power=self.total_power_w).tuple
            self.publish(payload=payload)
            time.sleep(1)

    