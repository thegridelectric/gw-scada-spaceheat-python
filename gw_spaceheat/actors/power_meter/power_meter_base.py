from typing import List

from actors.actor_base import ActorBase
from actors.mqtt_utils import QOS, Subscription
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker


class PowerMeterBase(ActorBase):
    def __init__(self, node: ShNode):
        super(PowerMeterBase, self).__init__(node=node)

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, client, userdata, message):
        self.screen_print(f"{message.topic} subscription not implemented!")

    def publish_gs_pwr(self, payload: GsPwr):
        topic = f'{self.node.alias}/{GsPwr_Maker.type_alias}'
        self.screen_print(f"Trying to publish {payload.as_type()} to topic {topic}")
        self.publish_client.publish(topic=topic, 
                                    payload=payload.as_type(),
                                    qos=QOS.AtMostOnce.value,
                                    retain=False)
