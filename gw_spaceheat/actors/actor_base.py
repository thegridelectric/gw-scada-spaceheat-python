import csv
import json
import os
import threading
import uuid
from abc import ABC, abstractmethod
from functools import cached_property
from typing import List

import paho.mqtt.client as mqtt

import helpers
import settings
from actors.utils import QOS, Subscription
from data_classes.sh_node import ShNode
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr import GsPwr
from schema.schema_switcher import TypeMakerByAliasDict


class ActorBase(ABC):
    @cached_property
    def atn_g_node_alias(cls):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[settings.WORLD_ROOT_ALIAS]["MyAtomicTNodeGNode"]
        return my_atn_as_dict["Alias"]

    @cached_property
    def atn_g_node_id(cls):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[settings.WORLD_ROOT_ALIAS]["MyAtomicTNodeGNode"]
        return my_atn_as_dict["GNodeId"]

    @cached_property
    def terminal_asset_g_node_alias(cls):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[settings.WORLD_ROOT_ALIAS]["MyTerminalAssetGNode"]
        return my_atn_as_dict["Alias"]

    @cached_property
    def terminal_asset_g_node_id(cls):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[settings.WORLD_ROOT_ALIAS]["MyTerminalAssetGNode"]
        return my_atn_as_dict["GNodeId"]

    @cached_property
    def scada_g_node_alias(cls):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_scada_as_dict = input_data[settings.WORLD_ROOT_ALIAS]["MyScadaGNode"]
        return my_scada_as_dict["Alias"]

    @cached_property
    def scada_g_node_id(cls):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_scada_as_dict = input_data[settings.WORLD_ROOT_ALIAS]["MyScadaGNode"]
        return my_scada_as_dict["GNodeId"]

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
        self.mqttBrokerPort = getattr(settings, "LOCAL_MQTT_BROKER_PORT", 1883)
        self.client_id = "-".join(str(uuid.uuid4()).split("-")[:-1])
        self.client = mqtt.Client(self.client_id)
        self.client.username_pw_set(
            username=settings.LOCAL_MQTT_USER_NAME,
            password=helpers.get_secret("LOCAL_MQTT_PW"),
        )
        self.client.on_message = self.on_mqtt_message
        self.client.on_connect = self.on_connect
        self.client.on_connect_fail = self.on_connect_fail
        self.client.on_disconnect = self.on_disconnect
        if self.logging_on:
            self.client.on_log = self.on_log
            self.client.enable_logger()

    def subscribe(self):
        subscriptions = list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.subscriptions()))
        if subscriptions:
            self.client.subscribe(subscriptions)

    def mqtt_log_hack(self, row):
        if self.logging_on:
            with open(self.log_csv, "a") as outfile:
                write = csv.writer(outfile, delimiter=",")
                write.writerow(row)

    # noinspection PyUnusedLocal
    def on_log(self, client, userdata, level, buf):
        self.mqtt_log_hack([f"({helpers.log_time()}) log: {buf}"])

    # noinspection PyUnusedLocal
    def on_connect(self, client, userdata, flags, rc):
        self.mqtt_log_hack(
            [
                f"({helpers.log_time()}) Local Mqtt client Connected flags {str(flags)} + result code {str(rc)}"
            ]
        )
        self.subscribe()

    # noinspection PyUnusedLocal
    def on_connect_fail(self, client, userdata):
        self.mqtt_log_hack([f"({helpers.log_time()}) Local Mqtt client Connect fail!"])

    # noinspection PyUnusedLocal
    def on_disconnect(self, client, userdata, rc):
        self.mqtt_log_hack(
            [f"({helpers.log_time()}) Local Mqtt client Disconnected! result code {str(rc)}"]
        )

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
                f"Type {type_alias} not recognized. Should be in TypeMakerByAliasDict keys!"
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
        topic = f"{self.node.alias}/{payload.TypeAlias}"
        self.client.publish(
            topic=topic,
            payload=payload.as_type(),
            qos=qos.value,
            retain=False,
        )
        # self.screen_print(f"published to {topic}")

    def terminate_main_loop(self):
        self._main_loop_running = False

    def start(self):
        self.client.connect(self.mqttBroker, port=self.mqttBrokerPort)
        self.client.loop_start()
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()
        self.screen_print(f"Started {self.__class__}")

    def stop(self):
        self.screen_print("Stopping ...")
        self.terminate_main_loop()
        self.client.disconnect()
        self.client.loop_stop()
        self.main_thread.join()
        self.screen_print("Stopped")

    @abstractmethod
    def main(self):
        raise NotImplementedError

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
