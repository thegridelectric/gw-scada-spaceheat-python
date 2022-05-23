from typing import List
from actors.primary_scada.primary_scada_base import PrimaryScadaBase
from data_classes.sh_node import ShNode
from data_classes.boolean_actuator_component import BooleanActuatorComponent 
from drivers.boolean_actuator.boolean_actuator_base import BooleanActuator
from schema.gt.gt_telemetry.gt_telemetry_1_0_0_maker import GtTelemetry100
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100
from drivers.boolean_actuator.ncd__pr8_14_spst__boolean_actuator import Ncd__Pr8_14_Spst__BooleanActuator
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator import Gridworks__SimBool30AmpRelay__BooleanActuator


class PrimaryScada(PrimaryScadaBase):
    def __init__(self, node: ShNode):
        super(PrimaryScada, self).__init__(node=node)
        self.power = 0
        self.consume_thread.start()
        self.total_power_w = 0
        house_nodes = list(self.node.parent.descendants)
        self.actuator_nodes: List[ShNode] = list(filter(lambda x: x.sh_node_role.alias == 'Actuator', house_nodes))
        self.relay_actuator: BooleanActuator = None
        self.set_relay_actuator()
        
    def set_relay_actuator(self):
        relay: ShNode = None
        relay = ShNode.by_alias['a.elt1.relay']
        primary_component: BooleanActuatorComponent = None
        primary_component = relay.primary_component
        if primary_component.make_and_model == 'NCD__PR8-14-SPST':
            self.relay_actuator =  Ncd__Pr8_14_Spst__BooleanActuator(component=primary_component)
        elif primary_component.make_and_model == 'GridWorks__SimBool30AmpRelay':
            self.relay_actuator = Gridworks__SimBool30AmpRelay__BooleanActuator(component=primary_component)
        else:
            raise NotImplementedError(f"No driver yet for {primary_component.make_and_model}")

    def publish(self):
        payload = GsPwr100_Maker(power=self.total_power_w).type
        self.publish_gs_pwr(payload=payload)

    def gs_pwr_100_from_powermeter(self, payload: GsPwr100):
        self.screen_print(f"Got {payload}")
        self.total_power_w = payload.Power
        self.publish()
    
    def gt_telemetry_100_received(self, payload: GtTelemetry100, from_node: ShNode):
        self.screen_print(f"Got {payload} from {from_node.alias}")

    @property
    def my_meter(self) ->ShNode:
        alias = self.node.alias.split('.')[0] + '.m'
        return ShNode.by_alias[alias]
    
    def turn_relay_on(self):
        self.relay_actuator.turn_on()

    def turn_relay_off(self):
        self.relay_actuator.turn_off()