import threading
import uuid
from abc import ABC, abstractmethod
from actors.mqtt_utils import QOS
from typing import List
import paho.mqtt.client as mqtt

import helpers
import settings
from data_classes.sh_node import ShNode

from actors.mqtt_utils import Subscription

from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry
from schema.gs.gs_pwr import GsPwr
from schema.gs.gs_dispatch import GsDispatch

class ActorBase(ABC):

    def __init__(self, node: ShNode):
        self.node = node
        self.logging_on = False
        self.mqttBroker = settings.LOCAL_MQTT_BROKER_ADDRESS
        self.publish_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.publish_client = mqtt.Client(self.publish_client_id)
        self.publish_client.username_pw_set(username=settings.LOCAL_MQTT_USER_NAME,
                                            password=helpers.get_secret('LOCAL_MQTT_PW'))
        self.publish_client.connect(self.mqttBroker)
        self.publish_client.loop_start()
        if self.logging_on:
            self.publish_client.on_log = self.on_log
        self.consume_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.consume_client = mqtt.Client(self.consume_client_id)
        self.consume_client.username_pw_set(username=settings.LOCAL_MQTT_USER_NAME,
                                            password=helpers.get_secret('LOCAL_MQTT_PW'))
        self.consume_client.connect(self.mqttBroker)
        if self.logging_on:
            self.consume_client.on_log = self.on_log
        self.consume_client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.subscriptions())))
        self.consume_client.on_message = self.on_message

    def on_log(self, client, userdata, level, buf):
        self.screen_print(f"log: {buf}")

    def consume(self):
        self.consume_client.loop_start()

    @abstractmethod
    def subscriptions(self) -> List[Subscription]:
        raise NotImplementedError

    @abstractmethod
    def on_message(self, client, userdata, message):
        raise NotImplementedError

    def publish(self, node: ShNode, payload_tuple: GtTelemetry):
        if type(payload_tuple) in [GsPwr, GsDispatch]:
            qos = QOS.AtMostOnce
        else:
            qos = QOS.AtLeastOnce
        self.publish_client.publish(
            topic=f'{node.alias}/{payload_tuple.TypeAlias}',
            payload=payload_tuple.as_type(),
            qos=qos,
            retain=False)

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)

