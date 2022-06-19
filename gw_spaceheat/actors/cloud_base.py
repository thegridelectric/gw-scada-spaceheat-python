import csv
import threading
import uuid
from abc import ABC, abstractmethod
from typing import List

import helpers
import load_house
import paho.mqtt.client as mqtt
import settings
from data_classes.sh_node import ShNode
from schema.gs.gs_dispatch_maker import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr
from schema.schema_switcher import TypeMakerByAliasDict
from actors.utils import QOS, Subscription


class CloudBase(ABC):
    def __init__(self, logging_on=False):
        self._main_loop_running = False
        self.main_thread = None
        self.logging_on = logging_on
        self.log_csv = f"output/debug_logs/cloudbase_{str(uuid.uuid4()).split('-')[1]}.csv"
        self.gwMqttBroker = settings.GW_MQTT_BROKER_ADDRESS
        self.gw_publish_client_id = "-".join(str(uuid.uuid4()).split("-")[:-1])
        self.gw_publish_client = mqtt.Client(self.gw_publish_client_id)
        self.gw_publish_client.username_pw_set(
            username=settings.GW_MQTT_USER_NAME,
            password=helpers.get_secret("GW_MQTT_PW"),
        )
        self.gw_publish_client.connect(self.gwMqttBroker)
        self.gw_publish_client.loop_start()
        if self.logging_on:
            self.gw_publish_client.on_log = self.on_log
        self.gw_consume_client_id = "-".join(str(uuid.uuid4()).split("-")[:-1])
        self.gw_consume_client = mqtt.Client(self.gw_consume_client_id)
        self.gw_consume_client.username_pw_set(
            username=settings.GW_MQTT_USER_NAME,
            password=helpers.get_secret("GW_MQTT_PW"),
        )
        self.gw_consume_client.on_message = self.on_gw_mqtt_message
        self.gw_consume_client.on_connect = self.on_connect
        self.gw_consume_client.on_connect_fail = self.on_connect_fail
        self.gw_consume_client.on_disconnect = self.on_disconnect
        self.gw_consume_client.connect(self.gwMqttBroker)
        if self.logging_on:
            self.gw_consume_client.on_log = self.on_log
        self.gw_consume_client.subscribe(
            list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.gw_subscriptions()))
        )

    @classmethod
    def load_sh_nodes(cls):
        load_house.load_all()

    def mqtt_log_hack(self, row):
        self.screen_print(row[0])
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
                f"({helpers.log_time()}) Publisher connected flags {str(flags)} + result code {str(rc)}"
            ]
        )

    # noinspection PyUnusedLocal
    def on_connect_fail(self, client, userdata, rc):
        self.mqtt_log_hack([f"({helpers.log_time()}) Connect fail! result code {str(rc)}"])

    # noinspection PyUnusedLocal
    def on_disconnect(self, client, userdata, rc):
        self.mqtt_log_hack(
            [f"({helpers.log_time()}) Publisher disconnected! result code {str(rc)}"]
        )

    @abstractmethod
    def gw_subscriptions(self) -> List[Subscription]:
        raise NotImplementedError

    def on_gw_mqtt_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split("/")
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias != helpers.scada_g_node_alias():
            raise Exception(f"alias {from_alias} not my Scada!")
        from_node = ShNode.by_alias["a.s"]
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
        self.gw_publish_client.publish(
            topic=f"{settings.ATN_G_NODE_ALIAS}/{payload.TypeAlias}",
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
        self.gw_consume_client.loop_start()
        self.gw_publish_client.loop_start()
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()
        self.screen_print(f"Started {self.__class__}")

    def stop(self):
        self.screen_print("Stopping ...")
        self.gw_consume_client.loop_stop()
        self.terminate_main_loop()
        self.main_thread.join()
        self.gw_publish_client.loop_stop()
        self.screen_print("Stopped")