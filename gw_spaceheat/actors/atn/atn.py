
from actors.atn.atn_base import Atn_Base
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr import GsPwr
from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry


class Atn(Atn_Base):
    def __init__(self, node: ShNode):
        super(Atn, self).__init__(node=node)
        self.gw_consume_thread.start()
        self.power = 0


    def publish(self):
        pass

    def gs_pwr_received(self, payload: GsPwr, from_g_node_alias: str):
        self.screen_print(f"Got {payload} from {from_g_node_alias}")
        self.power = payload.Power

    def gt_telemetry_received(self, payload: GtTelemetry, from_g_node_alias: str):
        self.screen_print(f"Got {payload} from {from_g_node_alias}")

    @property
    def my_scada(self) -> ShNode:
        alias = self.node.alias + '.s'
        return ShNode.by_alias[alias]
