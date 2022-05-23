
from typing import List
from actors.power_meter.power_meter_base import Power_Meter_Base
from actors.primary_scada.primary_scada_base import PrimaryScadaBase
from data_classes.sh_node import ShNode
from messages.gt_telemetry_1_0_0 import \
    Gt_Telemetry_1_0_0, TelemetryName
from messages.gs.gs_pwr_1_0_0 import Gs_Pwr_1_0_0, GsPwr100Payload

class Power_Meter(Power_Meter_Base):
    def __init__(self, node: ShNode):
        super(Power_Meter, self).__init__(node=node)
        self.consume_thread.start()
        self.total_power_w = 4230

    def publish(self):
        payload = Gs_Pwr_1_0_0(power=self.total_power_w).payload
        self.publish_gs_pwr(payload=payload)


    