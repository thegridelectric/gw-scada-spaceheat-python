import csv
import threading
import uuid
from abc import ABC
from abc import abstractmethod
from typing import List

import paho.mqtt.client as mqtt
from gwproto.messages import GsDispatch
from gwproto.messages import GsPwr

import helpers
from actors.utils import QOS
from actors.utils import Subscription
from actors2.config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from proactor.logger import MessageSummary
from schema.schema_switcher import TypeMakerByAliasDict


class ActorBase(ABC):

    def __init__(self, alias: str, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self._main_loop_running = False
        self.main_thread = None
        self.node = hardware_layout.node(alias)
        self.settings = settings
        self.layout = hardware_layout
        self.log_csv = f"{self.settings.paths.log_dir}/{self.node.alias}_{str(uuid.uuid4()).split('-')[1]}.csv"
        if self.settings.logging.verbose():
            row = [f"({helpers.log_time()}) {self.node.alias}"]
            with open(self.log_csv, "w") as outfile:
                write = csv.writer(outfile, delimiter=",")
                write.writerow(row)
            self.screen_print(f"log csv is {self.log_csv}")
        self.client_id = "-".join(str(uuid.uuid4()).split("-")[:-1])
        self.client = mqtt.Client(self.client_id)
        self.client.username_pw_set(
            username=self.settings.local_mqtt.username,
            password=self.settings.local_mqtt.password.get_secret_value(),
        )
        self.client.on_message = self.on_mqtt_message
        self.client.on_connect = self.on_connect
        self.client.on_connect_fail = self.on_connect_fail
        self.client.on_disconnect = self.on_disconnect
        if self.settings.logging.verbose():
            self.client.on_log = self.on_log
            self.client.enable_logger()

    def subscribe(self):
        subscriptions = list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.subscriptions()))
        if subscriptions:
            self.client.subscribe(subscriptions)

    def mqtt_log_hack(self, row):
        if self.settings.logging.verbose():
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
            topic = message.topic
            (from_alias, type_alias) = topic.split("/")
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias not in self.layout.nodes.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        from_node = self.layout.node(from_alias)
        if type_alias not in TypeMakerByAliasDict.keys():
            raise Exception(
                f"Type {type_alias} not recognized. Should be in TypeMakerByAliasDict keys!"
            )
        payload_as_tuple = TypeMakerByAliasDict[type_alias].type_to_tuple(message.payload)
        if self.settings.logging.verbose() or self.settings.logging.message_summary_enabled():
            print(MessageSummary.format("IN", self.node.alias, message.topic, payload_as_tuple))
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
        if self.settings.logging.verbose() or self.settings.logging.message_summary_enabled():
            print(MessageSummary.format("OUT", self.node.alias, topic, payload))
        self.client.publish(
            topic=topic,
            payload=payload.as_type(),
            qos=qos.value,
            retain=False,
        )

    def terminate_main_loop(self):
        self._main_loop_running = False

    def start_mqtt(self):
        self.client.connect(self.settings.local_mqtt.host, port=self.settings.local_mqtt.port)
        self.client.loop_start()

    def stop_mqtt(self):
        self.client.disconnect()
        self.client.loop_stop()

    def start(self):
        self.start_mqtt()
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()
        self.screen_print(f"Started {self.__class__}")

    def stop(self):
        self.terminate_main_loop()
        self.stop_mqtt()
        self.main_thread.join()
        self.screen_print(f"Stopped {self.__class__}")

    @abstractmethod
    def main(self):
        raise NotImplementedError

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)

    def all_power_tuples(self) -> List[TelemetryTuple]:
        return self.layout.all_power_tuples

    def all_metered_nodes(self) -> List[ShNode]:
        """All nodes whose power level is metered and included in power reporting by the Scada"""
        return self.layout.all_metered_nodes

    def all_resistive_heaters(self) -> List[ShNode]:
        return self.layout.all_resistive_heaters

    def all_power_meter_telemetry_tuples(self) -> List[TelemetryTuple]:
        return self.layout.all_power_meter_telemetry_tuples

    def power_meter_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role PowerMeter"""
        return self.layout.power_meter_node

    def scada_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role Scada"""
        return self.layout.scada_node

    def home_alone_node(self) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role HomeAlone"""
        return self.layout.home_alone_node

    @property
    def atn_g_node_alias(self):
        return self.layout.atn_g_node_alias

    @property
    def atn_g_node_id(self):
        return self.layout.atn_g_node_id

    @property
    def terminal_asset_g_node_alias(self):
        return self.layout.terminal_asset_g_node_alias

    @property
    def terminal_asset_g_node_id(self):
        return self.layout.terminal_asset_g_node_id

    @property
    def scada_g_node_alias(self):
        return self.layout.scada_g_node_alias

    @property
    def scada_g_node_id(self):
        return self.layout.scada_g_node_id
