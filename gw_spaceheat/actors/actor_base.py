import csv
import threading
import uuid
from abc import ABC, abstractmethod
from typing import List

import helpers
import paho.mqtt.client as mqtt
import settings
from data_classes.sh_node import ShNode
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr import GsPwr
from schema.schema_switcher import TypeMakerByAliasDict

from actors.utils import QOS, Subscription


class ActorBase(ABC):
    def __init__(self, node: ShNode, logging_on=False):
        self._main_loop_running = False
        self.main_thread = None
        self.node = node
        self.logging_on = logging_on
        self.log_csv = f"output/debug_logs/{self.node.alias}_{str(uuid.uuid4()).split('-')[1]}.csv"
        if self.logging_on:
            row = [f"({helpers.log_time()}) {self.node.alias}"]
            with open(self.log_csv, "w") as outfile:
                write = csv.writer(outfile, delimiter=",")
                write.writerow(row)
            self.screen_print(f"log csv is {self.log_csv}")
        self.mqttBroker = settings.LOCAL_MQTT_BROKER_ADDRESS
        self.publish_client_id = "-".join(str(uuid.uuid4()).split("-")[:-1])
        self.publish_client = mqtt.Client(self.publish_client_id)
        self.publish_client.username_pw_set(
            username=settings.LOCAL_MQTT_USER_NAME,
            password=helpers.get_secret("LOCAL_MQTT_PW"),
        )
        self.publish_client.on_connect = self.on_publish_connect
        self.publish_client.on_connect_fail = self.on_publish_connect_fail
        self.publish_client.on_disconnect = self.on_publish_disconnect
        self.publish_client.connect(self.mqttBroker)
        if self.logging_on:
            self.publish_client.on_log = self.on_log
        self.consume_client_id = "-".join(str(uuid.uuid4()).split("-")[:-1])
        self.consume_client = mqtt.Client(self.consume_client_id)
        self.consume_client.username_pw_set(
            username=settings.LOCAL_MQTT_USER_NAME,
            password=helpers.get_secret("LOCAL_MQTT_PW"),
        )
        self.consume_client.on_message = self.on_mqtt_message
        self.consume_client.on_connect = self.on_consume_connect
        self.consume_client.on_connect_fail = self.on_consume_connect_fail
        self.consume_client.on_disconnect = self.on_consume_disconnect
        self.consume_client.connect(self.mqttBroker)
        if self.logging_on:
            self.consume_client.on_log = self.on_log
        self.consume_client.subscribe(
            list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.subscriptions()))
        )

    def mqtt_log_hack(self, row):
        self.screen_print(row[0])
        if self.logging_on:
            with open(self.log_csv, "a") as outfile:
                write = csv.writer(outfile, delimiter=",")
                write.writerow(row)

    # noinspection PyUnusedLocal
    def on_log(self, client, userdata, level, buf):
        self.mqtt_log_hack([f"({helpers.log_time()}) log: {buf}"])

    # noinspection PyUnusedLocal
    def on_publish_connect(self, client, userdata, flags, rc):
        self.mqtt_log_hack(
            [f"({helpers.log_time()}) Local Publish Connected flags {str(flags)} + result code {str(rc)}"]
        )

    # noinspection PyUnusedLocal
    def on_publish_connect_fail(self, client, userdata, rc):
        self.mqtt_log_hack([f"({helpers.log_time()}) Local Publish Connect fail! result code {str(rc)}"])

    # noinspection PyUnusedLocal
    def on_publish_disconnect(self, client, userdata, rc):
        self.mqtt_log_hack([f"({helpers.log_time()}) Local Publish Disconnected! result code {str(rc)}"])
    
    # noinspection PyUnusedLocal
    def on_consume_connect(self, client, userdata, flags, rc):
        self.mqtt_log_hack(
            [f"({helpers.log_time()}) Local Consume Connected flags {str(flags)} + result code {str(rc)}"]
        )

    # noinspection PyUnusedLocal
    def on_consume_connect_fail(self, client, userdata, rc):
        self.mqtt_log_hack([f"({helpers.log_time()}) Local Consume Connect fail! result code {str(rc)}"])

    # noinspection PyUnusedLocal
    def on_consume_disconnect(self, client, userdata, rc):
        self.mqtt_log_hack([f"({helpers.log_time()}) Local Consume Disconnected! result code {str(rc)}"])

    @abstractmethod
    def subscriptions(self) -> List[Subscription]:
        raise NotImplementedError

    def on_mqtt_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split("/")
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias not in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        from_node = ShNode.by_alias[from_alias]
        if type_alias not in TypeMakerByAliasDict.keys():
            raise Exception(
                f"Type {type_alias} not recognized. Should be in TypeMkaerByAliasDict keys!"
            )
        payload_as_tuple = TypeMakerByAliasDict[type_alias].type_to_tuple(message.payload)
        self.on_message(from_node=from_node, payload=payload_as_tuple)

    @abstractmethod
    def on_message(self, from_node: ShNode, payload):
        raise NotImplementedError

    def publish(self, payload):
        if type(payload) in [GsPwr, GsDispatch]:
            qos = QOS.AtMostOnce
        else:
            qos = QOS.AtLeastOnce
        self.publish_client.publish(
            topic=f"{self.node.alias}/{payload.TypeAlias}",
            payload=payload.as_type(),
            qos=qos.value,
            retain=False,
        )

    def terminate_main_loop(self):
        self._main_loop_running = False

    def start(self):
        self.publish_client.loop_start()
        self.consume_client.loop_start()
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()
        self.screen_print(f"Started {self.__class__}")

    def stop(self):
        self.screen_print("Stopping ...")
        self.consume_client.loop_stop()
        self.terminate_main_loop()
        self.main_thread.join()
        self.publish_client.loop_stop()
        self.screen_print("Stopped")

    @abstractmethod
    def main(self):
        raise NotImplementedError

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
