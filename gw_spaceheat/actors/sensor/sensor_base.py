import json
from typing import List

from actors.actor_base import ActorBase
from actors.mqtt_utils import QOS, Subscription
from data_classes.sh_node import ShNode
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry, GtTelemetry_Maker


class SensorBase(ActorBase):
    def __init__(self, node: ShNode):
        super(SensorBase, self).__init__(node=node)

    def subscriptions(self) -> List[Subscription]:
        return []

    def on_message(self, client, userdata, message):
        self.screen_print(f"{message.topic} subscription not implemented!")

    def publish_gt_telemetry(self, payload: GtTelemetry):
        topic = f'{self.node.alias}/{GtTelemetry_Maker.type_alias}'
        self.screen_print(f"Trying to publish {payload.as_type()} to topic {topic}")
        self.publish_client.publish(topic=topic,
                                    payload=payload.as_type(),
                                    qos=QOS.AtLeastOnce.value,
                                    retain=False)
