from abc import abstractmethod, abstractproperty
import paho.mqtt.client as mqtt

from typing import List

from data_classes.sh_node import ShNode
from actors.actor_base import ActorBase
from actors.mqtt_utils import Subscription, QOS


from messages.gs.gs_pwr_1_0_0 import Gs_Pwr_1_0_0, GsPwr100Payload
from messages.gt_telemetry_1_0_0 import Gt_Telemetry_1_0_0
from messages.gt_telemetry_1_0_0_payload import GtTelemetry100Payload
class Atn_Base(ActorBase):
    def __init__(self, node: ShNode):
        super(Atn_Base, self).__init__(node=node)
    
    def subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{self.my_scada.alias}/{Gs_Pwr_1_0_0.mp_alias}',Qos=QOS.AtMostOnce),
                Subscription(Topic=f'{self.my_scada.alias}/{Gt_Telemetry_1_0_0.mp_alias}',Qos=QOS.AtLeastOnce)]

    def on_message(self, client, userdata, message):
        if message.topic == f'{self.my_scada.alias}/{Gs_Pwr_1_0_0.mp_alias}':
            payload = Gs_Pwr_1_0_0.binary_to_type(message.payload)
            self.gs_pwr_100_from_primaryscada(payload)
        elif message.topic == f'{self.my_scada.alias}/{Gt_Telemetry_1_0_0.mp_alias}':
            self.gt_telemetry_100_from_primaryscada(payload)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")
       
    @abstractmethod
    def gs_pwr_100_from_primaryscada(self, payload: GsPwr100Payload):
        raise NotImplementedError
     
    @abstractmethod
    def gt_telemetry_100_from_primaryscada(self, payload: GtTelemetry100Payload):
        raise NotImplementedError
    
    @abstractproperty
    def my_scada(self) -> ShNode:
        return NotImplementedError
       
    