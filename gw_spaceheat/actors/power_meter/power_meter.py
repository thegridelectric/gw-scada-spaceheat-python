
from actors.power_meter.power_meter_base import PowerMeterBase
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100


class PowerMeter(PowerMeterBase):
    def __init__(self, node: ShNode):
        super(PowerMeter, self).__init__(node=node)
        self.consume_thread.start()
        self.total_power_w = 4230

    def publish(self):
        payload = GsPwr100_Maker(power=self.total_power_w).type
        self.publish_gs_pwr(payload=payload)


    