import os
from abc import ABC, abstractmethod
import paho.mqtt.client as mqtt
import configparser
import threading
from typing import List
from data_classes.sh_node import ShNode
from actors.mqtt_utils import Subscription, QOS

class ActorBase(ABC):

    def __init__(self, node: ShNode):
        self.node = node
        config = configparser.ConfigParser()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        config.read(os.path.join(current_dir, '..', "config.ini"))
        self.mqttBroker = config["default"]["broker_address"]
        self.publish_client = mqtt.Client(f"{node.alias}-pub")
        self.publish_client.username_pw_set(config["default"]["username"], config["default"]["password"])
        self.publish_client.connect(self.mqttBroker)
        self.consume_client = mqtt.Client(f"{node.alias}")
        self.consume_client.username_pw_set(config["default"]["username"], config["default"]["password"])
        self.consume_client.connect(self.mqttBroker)
        self.consume_thread = threading.Thread(target=self.consume)


    def consume(self):
        print('hi')
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
