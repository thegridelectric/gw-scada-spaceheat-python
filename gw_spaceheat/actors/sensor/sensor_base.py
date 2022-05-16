import json
import time
from typing import List
from actors.actor_base import ActorBase


from data_classes.sh_node import ShNode
from data_classes.sensor_type_static import WATER_FLOW_METER
from data_classes.sh_node_role_static import SENSOR
from actors.mqtt_utils import Subscription, QOS

from messages.gt_telemetry_1_0_0 import \
    Gt_Telemetry_1_0_0, TelemetryName,  GtTelemetry100Payload

class SensorBase(ActorBase):
    def __init__(self, node: ShNode):
        super(SensorBase, self).__init__(node=node)  

    def subscriptions(self) -> List[Subscription]:
        return []
        
    def on_message(self, client, userdata, message):
        self.screen_print(f"{message.topic} subscription not implemented!")
    
    def publish_gt_telemetry_1_0_0(self, payload: GtTelemetry100Payload):
        topic = f'{self.node.alias}/{Gt_Telemetry_1_0_0.mp_alias}'
        self.publish_client.publish(topic=topic, 
                            payload=json.dumps(payload.asdict()),
                            qos = QOS.AtLeastOnce.value,
                            retain=True)
        self.screen_print(f"Just published {payload} to topic {topic}")

    
        