import time
from typing import Dict, List

from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from data_classes.sh_node import ShNode
from drivers.boolean_actuator.boolean_actuator_driver import \
    BooleanActuatorDriver
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver import \
    GridworksSimBool30AmpRelay_BooleanActuatorDriver
from drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver import \
    NcdPr814Spst_BooleanActuatorDriver
from schema.enums.make_model.make_model_map import MakeModel
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_telemetry.gt_telemetry_maker import (GtTelemetry,
                                                       GtTelemetry_Maker)

from actors.scada_base import ScadaBase
from actors.utils import QOS, Subscription


class Scada(ScadaBase):

    def __init__(self, node: ShNode):
        super(Scada, self).__init__(node=node)
        self.power = 0
        self.total_power_w = 0
        self.driver: Dict[ShNode, BooleanActuatorDriver] = {}
        self.temp_readings: List = []
        self.set_actuator_components()
        self.screen_print(f'Initialized {self.__class__}')

    def set_actuator_components(self):
        self.boost_actuator = ShNode.by_alias['a.elt1.relay']
        if self.boost_actuator.component.make_model == MakeModel.NCD__PR814SPST:
            self.driver[self.boost_actuator] = NcdPr814Spst_BooleanActuatorDriver(
                component=self.boost_actuator.component)
        elif self.boost_actuator.component.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver[self.boost_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(
                component=self.boost_actuator.component)
        else:
            raise NotImplementedError(f"No driver yet for {self.boost_actuator.component.make_model}")

        self.pump_actuator = ShNode.by_alias['a.tank.out.pump.relay']

        if self.pump_actuator.component.make_model == MakeModel.NCD__PR814SPST:
            self.driver[self.pump_actuator] = NcdPr814Spst_BooleanActuatorDriver(
                component=self.pump_actuator.component)
        elif self.pump_actuator.component.make_model == MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY:
            self.driver[self.pump_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(
                component=self.pump_actuator.component)
        else:
            raise NotImplementedError(f"No driver yet for {self.pump_actuator.component.make_model}")

    ################################################
    # Receiving messages
    ###############################################

    def subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'a.m/{GsPwr_Maker.type_alias}', Qos=QOS.AtMostOnce),
                Subscription(Topic=f'a.tank.out.flowmeter1/{GtTelemetry_Maker.type_alias}', Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp0/{GtTelemetry_Maker.type_alias}', Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp1/{GtTelemetry_Maker.type_alias}', Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp2/{GtTelemetry_Maker.type_alias}', Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp3/{GtTelemetry_Maker.type_alias}', Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp4/{GtTelemetry_Maker.type_alias}', Qos=QOS.AtLeastOnce)]

    def on_message(self, from_node: ShNode, payload):
        if isinstance(payload, GsPwr):
            self.gs_pwr_received(from_node, payload)
        elif isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
        elif isinstance(payload, GtTelemetry):
            self.gt_telemetry_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_pwr_received(self, from_node: ShNode, payload: GsPwr):
        if from_node != ShNode.by_alias['a.m']:
            raise Exception("Need to track all metering and make sure we have the sum")
        self.screen_print(f"Got {payload}")
        self.total_power_w = payload.Power
        self.gw_publish(payload=payload)

    def gt_telemetry_received(self, from_node: ShNode, payload: GtTelemetry):
        self.screen_print(f"{payload.Value} from {from_node.alias}")

    def on_gw_message(self, from_node: ShNode, payload: GtTelemetry):
        if from_node != ShNode.by_alias['a']:
            raise Exception("gw messages must come from the remote AtomicTNode!")
        if isinstance(payload, GsDispatch):
            self.gs_dispatch_received(from_node, payload)
        else:
            self.screen_print(f"{payload} subscription not implemented!")

    def gs_dispatch_received(self, from_node: ShNode, payload: GsDispatch):
        raise NotImplementedError

    ################################################
    # Primary functions
    ###############################################
    
    def turn_on(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_on()

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_off()

    def main(self):
        self._main_loop_running = True
        while self._main_loop_running is True:
            # track time and send status every x minutes (likely 5)
            time.sleep(1)