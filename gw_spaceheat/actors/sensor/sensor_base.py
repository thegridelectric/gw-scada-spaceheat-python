import json
import time
from typing import List
from actors.actor_base import ActorBase
from data_classes.sh_node import ShNode
from data_classes.sensor_type_static import WATER_FLOW_METER
from data_classes.sh_node_role_static import SENSOR
from actors.mqtt_utils import Subscription, QOS
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import GtTelemetry101, GtTelemetry101_Maker


class SensorBase(ActorBase):
    def __init__(self, node: ShNode):
        super(SensorBase, self).__init__(node=node)  

    def subscriptions(self) -> List[Subscription]:
        return []
        
    def on_message(self, client, userdata, message):
        self.screen_print(f"{message.topic} subscription not implemented!")
    
    def publish_gt_telemetry_1_0_1(self, payload: GtTelemetry101):
        self.screen_print(f"Trying to publish")
        topic = f'{self.node.alias}/{GtTelemetry101_Maker.mp_alias}'
        self.publish_client.publish(topic=topic, 
                            payload=json.dumps(payload.asdict()),
                            qos = QOS.AtLeastOnce.value,
                            retain=False)


    
        