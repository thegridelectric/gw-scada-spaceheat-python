from abc import abstractmethod
import paho.mqtt.client as mqtt

from typing import List
from actors.actor_base import ActorBase
from data_classes.sh_node import ShNode
from actors.mqtt_utils import Subscription, QOS

from messages.gs.gs_pwr_1_0_0 import Gs_Pwr_1_0_0, GsPwr100Payload

class Power_Meter_Base(ActorBase):
    def __init__(self, node: ShNode):
        super(Power_Meter_Base, self).__init__(node=node)

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, client, userdata, message):
        self.screen_print(f"{message.topic} subscription not implemented!")

    def publish_gs_pwr(self, payload: GsPwr100Payload):
        topic = f'{self.node.alias}/{Gs_Pwr_1_0_0.mp_alias}'
        self.publish_client.publish(topic=topic, 
                            payload=payload.asbinary(),
                            qos = QOS.AtMostOnce.value,
                            retain=False)
        self.screen_print(f"Just published {payload} to topic {topic}")
