from abc import abstractmethod, abstractproperty
import paho.mqtt.client as mqtt
import json
from typing import List
from actors.actor_base import ActorBase
from data_classes.sh_node import ShNode
from actors.mqtt_utils import Subscription, QOS

from messages.gs.gs_pwr_1_0_0 import Gs_Pwr_1_0_0, GsPwr100Payload
from messages.gt_telemetry_1_0_0 import Gt_Telemetry_1_0_0, GtTelemetry100Payload
class Primary_Scada_Base(ActorBase):
    def __init__(self, node: ShNode):
        super(Primary_Scada_Base, self).__init__(node=node)

    def subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{self.my_meter.alias}/{Gs_Pwr_1_0_0.mp_alias}',Qos=QOS.AtMostOnce),
                Subscription(Topic=f'a.tank.out.flowmeter1/{Gt_Telemetry_1_0_0.mp_alias}',Qos=QOS.AtLeastOnce)]

    def on_message(self, client, userdata, message):
        try:
            (from_alias, mp_alias) = message.topic.split('/')
        except:
            raise Exception(f"topic must be of format A/B")
        if not from_alias in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        if mp_alias == Gs_Pwr_1_0_0.mp_alias:
            self.raw_payload = message.payload
            payload = Gs_Pwr_1_0_0.binary_to_type(message.payload)
            self.gs_pwr_100_from_powermeter(payload)
        elif mp_alias == Gt_Telemetry_1_0_0.mp_alias:
            payload = Gt_Telemetry_1_0_0.create_payload_from_camel_dict(json.loads(message.payload))
            from_node = ShNode.by_alias[from_alias]
            self.gt_telemetry_100_received(payload=payload, from_node=from_node)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")
        
    @abstractmethod
    def gs_pwr_100_from_powermeter(self, payload: GsPwr100Payload):
        raise NotImplementedError
    
    @abstractmethod
    def gt_telemetry_100_received(self, payload: GtTelemetry100Payload, from_node: ShNode):
        raise NotImplementedError

    def publish_gs_pwr(self, payload: GsPwr100Payload):
        topic = f'{self.node.alias}/{Gs_Pwr_1_0_0.mp_alias}'
        self.publish_client.publish(topic=topic, 
                            payload=payload.asbinary(),
                            qos = QOS.AtMostOnce.value,
                            retain=False)
        self.screen_print(f"Just published {payload} to topic {topic}")

    @abstractproperty
    def my_meter(self) ->ShNode:
        raise NotImplementedError