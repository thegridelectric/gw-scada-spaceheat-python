
from actors.atn_base import Atn_Base
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr import GsPwr
from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry


class Atn(Atn_Base):
    def __init__(self, node: ShNode):
        super(Atn, self).__init__(node=node)
        self.total_power_w = 0
        self.gw_consume()
        self.screen_print(f'Started {self.__class__}')

    def gs_pwr_received(self, payload: GsPwr, from_g_node_alias: str):
        self.screen_print(f"Got {payload} from {from_g_node_alias}")
        self.total_power_w = payload.Power

