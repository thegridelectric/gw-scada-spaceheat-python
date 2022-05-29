from typing import List, Dict
from actors.primary_scada.primary_scada_base import PrimaryScadaBase
from data_classes.sh_node import ShNode
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent 
from drivers.boolean_actuator.boolean_actuator_driver import BooleanActuatorDriver
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import GtTelemetry101, TelemetryName
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100
from drivers.boolean_actuator.ncd__pr814spst__boolean_actuator_driver import NcdPr814Spst_BooleanActuatorDriver
from drivers.boolean_actuator.gridworks_simbool30amprelay__boolean_actuator_driver import GridworksSimBool30AmpRelay_BooleanActuatorDriver


class PrimaryScada(PrimaryScadaBase):
    def __init__(self, node: ShNode):
        super(PrimaryScada, self).__init__(node=node)
        self.power = 0
        self.consume_thread.start()
        self.total_power_w = 0
        self.driver: Dict[ShNode, BooleanActuatorDriver] = {}
        self.set_actuator_components()
        self.temp_readings: List = []
        
        
    def set_actuator_components(self):
        """
        TODO: pick out the actuators programatically, starting with this. For now, hand-selecting 2 boolean actuators.
        house_nodes = list(self.node.parent.descendants)
        self.actuator_nodes: List[ShNode] = list(filter(lambda x: x.sh_node_role.alias == 'Actuator', house_nodes))
        """


        self.boost_actuator = ShNode.by_alias['a.elt1.relay']
        if self.boost_actuator.primary_component.make_model == 'NCD__PR8-14-SPST':
            self.driver[self.boost_actuator] =  NcdPr814Spst_BooleanActuatorDriver(component=self.boost_actuator.primary_component)
        elif self.boost_actuator.primary_component.make_model == 'GridWorks__SimBool30AmpRelay':
            self.driver[self.boost_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(component=self.boost_actuator.primary_component)
        else:
            raise NotImplementedError(f"No driver yet for {self.boost_actuator.primary_component.make_model}")

        self.pump_actuator = ShNode.by_alias['a.tank.out.pump.relay']

        if self.pump_actuator.primary_component.make_model == 'NCD__PR8-14-SPST':
            self.driver[self.pump_actuator] =  NcdPr814Spst_BooleanActuatorDriver(component=self.pump_actuator.primary_component)
        elif self.pump_actuator.primary_component.make_model == 'GridWorks__SimBool30AmpRelay':
            self.driver[self.pump_actuator] = GridworksSimBool30AmpRelay_BooleanActuatorDriver(component=self.pump_actuator.primary_component)
        else:
            raise NotImplementedError(f"No driver yet for {self.pump_actuator.primary_component.make_model}")
        

    def publish(self):
        payload = GsPwr100_Maker(power=self.total_power_w).type
        self.publish_gs_pwr(payload=payload)

    def gs_pwr_100_from_powermeter(self, payload: GsPwr100):
        self.screen_print(f"Got {payload}")
        self.total_power_w = payload.Power
        self.publish()
    
    def gt_telemetry_100_received(self, payload: GtTelemetry101, from_node: ShNode):
        self.screen_print(f"Got {payload} from {from_node.alias}")
        self.payload = payload


    @property
    def my_meter(self) ->ShNode:
        alias = self.node.alias.split('.')[0] + '.m'
        return ShNode.by_alias[alias]
    
    def turn_on(self, ba: ShNode):
        if not isinstance(ba.primary_component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_on()

    def turn_off(self, ba: ShNode):
        if not isinstance(ba.primary_component, BooleanActuatorComponent):
            raise Exception(f"{ba} must be a BooleanActuator!")
        if ba.has_actor:
            raise NotImplementedError('No actor for boolean actuator yet')
        else:
            self.driver[ba].turn_off()