from typing import List
from actors.power_meter.power_meter_base import Power_Meter_Base
from actors.primary_scada.primary_scada_base import PrimaryScadaBase
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100


class Power_Meter(Power_Meter_Base):
    def __init__(self, node: ShNode):
        super(Power_Meter, self).__init__(node=node)
        self.consume_thread.start()
        self.total_power_w = 4230

    def publish(self):
        payload = GsPwr100_Maker(power=self.total_power_w).type
        self.publish_gs_pwr(payload=payload)


    