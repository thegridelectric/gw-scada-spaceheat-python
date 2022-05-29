
from actors.atn.atn_base import Atn_Base
from data_classes.sh_node import ShNode

from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import  GtTelemetry101
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100

class Atn(Atn_Base):
    def __init__(self, node: ShNode):
        super(Atn, self).__init__(node=node)
        self.consume_thread.start() 
        self.payloads = []
        self.power = 0


    def publish(self):
        pass

    def gs_pwr_100_from_primaryscada(self, payload: GsPwr100):
        self.power = payload.Power
        self.screen_print(f"Power is {self.power}")

    def gt_telemetry_100_from_primaryscada(self, payload: GtTelemetry101):
        self.screen_print(f"Got {payload}")

    @property
    def my_scada(self) -> ShNode:
        alias = self.node.alias + '.s'
        #TODO - look for child with role PrimaryScada
        return ShNode.by_alias[alias]