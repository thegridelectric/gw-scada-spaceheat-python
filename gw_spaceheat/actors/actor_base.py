import threading
import uuid
from abc import ABC, abstractmethod
from typing import List
import paho.mqtt.client as mqtt

import helpers
import settings
from data_classes.sh_node import ShNode

from actors.mqtt_utils import Subscription


class ActorBase(ABC):

    def __init__(self, node: ShNode):
        self.node = node
        self.logging_on = False
        self.mqttBroker = settings.LOCAL_MQTT_BROKER_ADDRESS
        self.publish_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.publish_client = mqtt.Client(self.publish_client_id)
        self.publish_client.username_pw_set(username=settings.LOCAL_MQTT_USER_NAME, password=helpers.get_secret('LOCAL_MQTT_PW'))
        self.publish_client.connect(self.mqttBroker)
        self.publish_client.loop_start()
        if self.logging_on:
            self.publish_client.on_log = self.on_log
        self.consume_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.consume_client = mqtt.Client(self.consume_client_id)
        self.consume_client.username_pw_set(username=settings.LOCAL_MQTT_USER_NAME, password=helpers.get_secret('LOCAL_MQTT_PW'))
        self.consume_client.connect(self.mqttBroker)
        if self.logging_on:
            self.consume_client.on_log = self.on_log
        self.consume_thread = threading.Thread(target=self.consume)

    def on_log(self, client, userdata, level, buf):
        self.screen_print(f"log: {buf}")

    def consume(self):
        self.consume_client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.subscriptions())))
        self.consume_client.on_message = self.on_message
        self.consume_client.loop_forever()

    @abstractmethod
    def subscriptions(self) -> List[Subscription]:
        raise NotImplementedError

    @abstractmethod
    def on_message(self, client, userdata, message):
        raise NotImplementedError

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
