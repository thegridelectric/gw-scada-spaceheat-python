from typing import List
from actors.primary_scada.primary_scada_base import Primary_Scada_Base
from data_classes.sh_node import ShNode
from data_classes.actuator_component import ActuatorComponent
from drivers.boolean_actuator.boolean_actuator_base import BooleanActuator
from messages.gt_telemetry_1_0_0 import \
    Gt_Telemetry_1_0_0, TelemetryName
from messages.gs.gs_pwr_1_0_0 import Gs_Pwr_1_0_0, GsPwr100Payload
from messages.gt_telemetry_1_0_0 import Gt_Telemetry_1_0_0, GtTelemetry100Payload
from drivers.boolean_actuator.ncd__pr8_14_spst__boolean_actuator import Ncd__Pr8_14_Spst__BooleanActuator

class Primary_Scada(Primary_Scada_Base):
    def __init__(self, node: ShNode):
        super(Primary_Scada, self).__init__(node=node)
        self.power = 0
        self.consume_thread.start()
        self.total_power_w = 0
        self.relay_actuator: BooleanActuator = None
        self.set_relay_actuator()
        
    def set_relay_actuator(self):
        relay: ShNode = None
        relay = ShNode.by_alias['a.elt1.relay']
        primary_component: ActuatorComponent = None
        primary_component = relay.primary_component
        if primary_component.make_and_model == 'NCD__PR8-14-SPST':
            self.relay_actuator =  Ncd__Pr8_14_Spst__BooleanActuator(component=primary_component)
        else:
            raise NotImplementedError(f"No driver yet for {primary_component.make_and_model}")

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
    
    def turn_relay_on(self):
        self.relay_actuator.turn_on()

    def turn_relay_off(self):
        self.relay_actuator.turn_off()