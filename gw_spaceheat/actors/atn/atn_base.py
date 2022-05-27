from abc import abstractmethod, abstractproperty
import paho.mqtt.client as mqtt

from typing import List

from data_classes.sh_node import ShNode
from actors.actor_base import ActorBase
from actors.mqtt_utils import Subscription, QOS


from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import  GtTelemetry101_Maker, GtTelemetry101
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100


class Atn_Base(ActorBase):
    def __init__(self, node: ShNode):
        super(Atn_Base, self).__init__(node=node)
    
    def subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{self.my_scada.alias}/{GsPwr100_Maker.mp_alias}',Qos=QOS.AtMostOnce),
                Subscription(Topic=f'{self.my_scada.alias}/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce)]

    def on_message(self, client, userdata, message):
        if message.topic == f'{self.my_scada.alias}/{GsPwr100_Maker.mp_alias}':
            payload = GsPwr100_Maker.binary_to_type(message.payload)
            self.gs_pwr_100_from_primaryscada(payload)
        # Not implemented
        # elif message.topic == f'{self.my_scada.alias}/{GtTelemetry101_Maker.mp_alias}':
            # self.gt_telemetry_100_from_primaryscada(payload)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")
       
    @abstractmethod
    def gs_pwr_100_from_primaryscada(self, payload: GsPwr100):
        raise NotImplementedError
     
    @abstractmethod
    def gt_telemetry_100_from_primaryscada(self, payload: GtTelemetry101):
        raise NotImplementedError
    
    @abstractproperty
    def my_scada(self) -> ShNode:
        return NotImplementedError
       
    