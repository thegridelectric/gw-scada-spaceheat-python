
import time
from typing import List

from actors.actor_base import ActorBase
from actors.utils import Subscription
from data_classes.sh_node import ShNode
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker


class PipeFlowMeter(ActorBase):
    def __init__(self, node: ShNode):
        super(PipeFlowMeter, self).__init__(node=node)
        self.water_flow_gpm = 0
        self.consume()
        self.screen_print(f'Started {self.__class__}')

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, from_node: ShNode, payload):
        pass

    def test_publish(self):
        self.water_flow_gpm += 100
        self.water_flow_gpm = self.water_flow_gpm % 3000
        payload = GtTelemetry_Maker(name=TelemetryName.WATER_FLOW_GPM_TIMES100,
                                    value=int(self.water_flow_gpm * 100),
                                    exponent=0,
                                    scada_read_time_unix_ms=int(time.time() * 1000)).tuple
        self.publish(payload=payload)
        
    def consume(self):
        pass