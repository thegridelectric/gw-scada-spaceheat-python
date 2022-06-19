
import time
from typing import List
import uuid
import helpers
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_dispatch.gt_dispatch_maker import GtDispatch_Maker
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import (
    GtShSimpleStatus, GtShSimpleStatus_Maker)

from actors.cloud_base import CloudBase
from actors.utils import QOS, Subscription


class Atn(CloudBase):
    def __init__(self, node: ShNode, logging_on=False):
        super(Atn, self).__init__(logging_on=logging_on)
        self.node = node
        self.log_csv = f"output/debug_logs/atn_{str(uuid.uuid4()).split('-')[1]}.csv"
        self.total_power_w = 0
        self.screen_print(f'Initialized {self.__class__}')

    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{helpers.scada_g_node_alias()}/{GsPwr_Maker.type_alias}', Qos=QOS.AtMostOnce),
                Subscription(Topic=f'{helpers.scada_g_node_alias()}/{GtShSimpleStatus_Maker.type_alias}',
                             Qos=QOS.AtLeastOnce)]

    def on_gw_message(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias['a.s']:
            raise Exception("gw messages must come from the Scada!")
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GtShSimpleStatus):
            self.gt_spaceheat_status_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        self.total_power_w = payload.Power

    def gt_spaceheat_status_received(self, from_node: ShNode, payload: GtShSimpleStatus):
        self.screen_print("Got status!")

    ################################################
    # Primary functions
    ###############################################

    def turn_on(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        payload = GtDispatch_Maker(
            relay_state=1,
            sh_node_alias=ba.alias).tuple
        self.gw_publish(payload)

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        payload = GtDispatch_Maker(
            relay_state=0,
            sh_node_alias=ba.alias).tuple
        self.gw_publish(payload)

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            time.sleep(1)

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
