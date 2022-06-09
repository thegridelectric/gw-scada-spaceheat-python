
from actors.atn.atn_base import Atn_Base
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import GtTelemetry101


class Atn(Atn_Base):
    def __init__(self, node: ShNode):
        super(Atn, self).__init__(node=node)
        self.gw_consume_thread.start() 
        self.payloads = []
        self.power = 0

    def publish(self):
        pass

    def gs_pwr_100_received(self, payload: GsPwr100, from_node: ShNode):
        raise NotImplementedError
     
    def gt_telemetry_100_received(self, payload: GtTelemetry101, from_node: ShNode):
        raise NotImplementedError


    @property
    def my_scada(self) -> ShNode:
        alias = self.node.alias + '.s'
        return ShNode.by_alias[alias]
