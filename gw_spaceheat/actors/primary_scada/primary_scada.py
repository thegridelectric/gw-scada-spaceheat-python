from typing import List
from actors.primary_scada.primary_scada_base import Primary_Scada_Base
from data_classes.sh_node import ShNode
from messages.gt_telemetry_1_0_0 import \
    Gt_Telemetry_1_0_0, TelemetryName
from messages.gs.gs_pwr_1_0_0 import Gs_Pwr_1_0_0, GsPwr100Payload
from messages.gt_telemetry_1_0_0 import Gt_Telemetry_1_0_0, GtTelemetry100Payload
class Primary_Scada(Primary_Scada_Base):
    def __init__(self, node: ShNode):
        super(Primary_Scada, self).__init__(node=node)
        self.power = 0
        self.consume_thread.start()
        self.total_power_w = 0

    def publish(self):
        payload = Gs_Pwr_1_0_0(power=self.total_power_w).payload
        self.publish_gs_pwr(payload=payload)

    def gs_pwr_100_from_powermeter(self, payload: GsPwr100Payload):
        self.screen_print(f"Got {payload}")
        self.total_power_w = payload.Power
        self.publish()
    
    def gt_telemetry_100_received(self, payload: GtTelemetry100Payload, from_node: ShNode):
        self.screen_print(f"Got {payload} from {from_node.alias}")

    @property
    def my_meter(self) ->ShNode:
        alias = self.node.alias.split('.')[0] + '.m'
        return ShNode.by_alias[alias]