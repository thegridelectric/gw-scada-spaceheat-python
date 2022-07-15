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
from config import ScadaSettings
from actors.utils import QOS, Subscription
from data_classes.sh_node import ShNode
from schema.gs.gs_dispatch_maker import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr
from schema.schema_switcher import TypeMakerByAliasDict


class CloudBase(ABC):
    @cached_property
    def atn_g_node_alias(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[self.settings.world_root_alias]["MyAtomicTNodeGNode"]
        return my_atn_as_dict["Alias"]

    @cached_property
    def atn_g_node_id(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[self.settings.world_root_alias]["MyAtomicTNodeGNode"]
        return my_atn_as_dict["GNodeId"]

    @cached_property
    def terminal_asset_g_node_alias(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[self.settings.world_root_alias]["MyTerminalAssetGNode"]
        return my_atn_as_dict["Alias"]

    @cached_property
    def terminal_asset_g_node_id(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_atn_as_dict = input_data[self.settings.world_root_alias]["MyTerminalAssetGNode"]
        return my_atn_as_dict["GNodeId"]

    @cached_property
    def scada_g_node_alias(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_scada_as_dict = input_data[self.settings.world_root_alias]["MyScadaGNode"]
        return my_scada_as_dict["Alias"]


    @cached_property
    def scada_g_node_id(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "../input_data/houses.json"), "r") as read_file:
            input_data = json.load(read_file)
        my_scada_as_dict = input_data[self.settings.world_root_alias]["MyScadaGNode"]
        return my_scada_as_dict["GNodeId"]

    def __init__(self, settings: ScadaSettings):
        self._main_loop_running = False
        self.main_thread = None
        self.settings = settings
        self.log_csv = f"{self.settings.output_dir}/debug_logs/cloudbase_{str(uuid.uuid4()).split('-')[1]}.csv"
        self.gw_client_id = "-".join(str(uuid.uuid4()).split("-")[:-1])
        self.gw_client = mqtt.Client(self.gw_client_id)
        self.gw_client.username_pw_set(
            username=settings.gridworks_mqtt.username,
            password=settings.gridworks_mqtt.password.get_secret_value(),
        )
        self.gw_client.on_message = self.on_gw_mqtt_message
        self.gw_client.on_connect = self.on_connect
        self.gw_client.on_connect_fail = self.on_connect_fail
        self.gw_client.on_disconnect = self.on_disconnect
        if self.settings.logging_on:
            self.gw_client.on_log = self.on_log
            self.gw_client.enable_logger()

    def subscribe_gw(self):
        self.gw_client.subscribe(
            list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.gw_subscriptions()))
        )

    def mqtt_log_hack(self, row):
        if self.settings.logging_on:
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
                f"({helpers.log_time()}) Mqtt client Connected flags {str(flags)} + result code {str(rc)}"
            ]
        )
        self.subscribe_gw()

    # noinspection PyUnusedLocal
    def on_connect_fail(self, client, userdata):
        self.mqtt_log_hack([f"({helpers.log_time()}) Mqtt client Connect fail"])

    # noinspection PyUnusedLocal
    def on_disconnect(self, client, userdata, rc):
        self.mqtt_log_hack(
            [f"({helpers.log_time()}) Mqtt client disconnected! result code {str(rc)}"]
        )

    @abstractmethod
    def gw_subscriptions(self) -> List[Subscription]:
        raise NotImplementedError

    def on_gw_mqtt_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split("/")
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias != self.scada_g_node_alias and from_alias != self.atn_g_node_alias:
            raise Exception(f"alias {from_alias} not my Scada or Atn!")
        if from_alias == self.scada_g_node_alias:
            from_node = ShNode.by_alias["a.s"]
        else:
            from_node = ShNode.by_alias["a"]
        if type_alias not in TypeMakerByAliasDict.keys():
            raise Exception(
                f"Type {type_alias} not recognized. Should be in TypeMakerByAliasDict keys!"
            )
        payload_as_tuple = TypeMakerByAliasDict[type_alias].type_to_tuple(message.payload)
        self.on_gw_message(from_node=from_node, payload=payload_as_tuple)

    @abstractmethod
    def on_gw_message(self, from_node: ShNode, payload):
        raise NotImplementedError

    def gw_publish(self, payload):
        if type(payload) in [GsPwr, GsDispatch]:
            qos = QOS.AtMostOnce
        else:
            qos = QOS.AtLeastOnce
        self.gw_client.publish(
            topic=f"{self.atn_g_node_alias}/{payload.TypeAlias}",
            payload=payload.as_type(),
            qos=qos.value,
            retain=False,
        )

    def terminate_main_loop(self):
        self._main_loop_running = False

    @abstractmethod
    def screen_print(self, note):
        raise NotImplementedError

    @abstractmethod
    def main(self):
        raise NotImplementedError

    def start(self):
        self.gw_client.connect(
            self.settings.gridworks_mqtt.host,
            port=self.settings.gridworks_mqtt.port
        )
        self.gw_client.loop_start()
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()
        self.screen_print(f"Started {self.__class__}")

    def stop(self):
        self.screen_print("Stopping ...")
        self.terminate_main_loop()
        self.gw_client.disconnect()
        self.gw_client.loop_stop()
        self.main_thread.join()
        self.screen_print("Stopped")
