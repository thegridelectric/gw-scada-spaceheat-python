import csv
import json
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from typing import List

import paho.mqtt.client as mqtt

import helpers
from actors2.scada2 import ScadaMessageDecoder
from config import ScadaSettings
from actors.utils import QOS, Subscription, gw_mqtt_topic_encode, gw_mqtt_topic_decode
from proactor.logger import MessageSummary
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from schema.decoders_factory import DecoderExtractor, OneDecoderExtractor, PydanticExtractor
from schema.gs.gs_dispatch_maker import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gt.gt_sh_status.gt_sh_status_maker import GtShStatus_Maker
from schema.gt.snapshot_spaceheat.snapshot_spaceheat_maker import SnapshotSpaceheat_Maker
from schema.schema_switcher import TypeMakerByAliasDict


class CloudBase(ABC):

    def __init__(self, settings: ScadaSettings, hardware_layout: HardwareLayout):
        self._main_loop_running = False
        self.main_thread = None
        self.settings = settings
        self.layout = hardware_layout
        self.logger = logging.getLogger(settings.logging.base_log_name)
        self.log_csv = f"{self.settings.paths.log_dir}/cloudbase_{str(uuid.uuid4()).split('-')[1]}.csv"
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
        self.decoders = DecoderExtractor(extractors=[
            OneDecoderExtractor(decoder_function_name="type_to_tuple"),
            PydanticExtractor(decoder_function_name="parse_raw"),
        ]).from_objects(
            [
                GtShStatus_Maker,
                SnapshotSpaceheat_Maker,
            ],
            message_payload_discriminator=ScadaMessageDecoder,
        ).add_decoder(
            "p",
            lambda decoded: GsPwr_Maker(json.loads(decoded)[0]).tuple
        )


    def subscribe_gw(self):
        subscriptions = list(map(lambda x: (f"{gw_mqtt_topic_encode(x.Topic)}", x.Qos.value), self.gw_subscriptions()))
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(f"Subscriptions: {len(subscriptions)}")
            for subscription in subscriptions:
                self.logger.info(f"\t{subscription[0]}")
        self.gw_client.subscribe(subscriptions)

    def mqtt_log_hack(self, row):
        self.logger.info(row)
        if self.settings.logging.verbose():
            with open(self.log_csv, "a") as outfile:
                write = csv.writer(outfile, delimiter=",")
                write.writerow(row)

    # noinspection PyUnusedLocal
    def on_log(self, client, userdata, level, buf):
        self.logger.info(buf)

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
        self.logger.info(f"++on_gw_mqtt_message: {message.topic}")
        path_dbg = 0
        try:
            topic = gw_mqtt_topic_decode(message.topic)
            (from_alias, type_alias) = topic.split("/")
            path_dbg |= 0x00000001
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias != self.scada_g_node_alias and from_alias != self.atn_g_node_alias:
            raise Exception(f"alias {from_alias} not my Scada or Atn!")
        if from_alias == self.scada_g_node_alias:
            path_dbg |= 0x00000002
            from_node = self.layout.node("a.s")
        else:
            path_dbg |= 0x00000004
            from_node = self.layout.node("a")
        if type_alias not in TypeMakerByAliasDict.keys():
            path_dbg |= 0x00000008
            payload_as_tuple = self.decoders.decode_str(type_alias, message.payload).payload
        else:
            path_dbg |= 0x00000010
            payload_as_tuple = TypeMakerByAliasDict[type_alias].type_to_tuple(message.payload)

        if self.settings.logging.verbose() or self.settings.logging.message_summary_enabled():
            path_dbg |= 0x00000020
            self.logger.info(
                MessageSummary.format(
                    "IN",
                    self.atn_g_node_alias,
                    message.topic,
                    payload_as_tuple,
                    broker_flag="*"
                )
            )
        self.on_gw_message(from_node=from_node, payload=payload_as_tuple)
        self.logger.info(f"--on_gw_mqtt_message: path: 0x{path_dbg:08X}")


    @abstractmethod
    def on_gw_message(self, from_node: ShNode, payload):
        raise NotImplementedError

    def gw_publish(self, payload):
        if type(payload) in [GsPwr, GsDispatch]:
            qos = QOS.AtMostOnce
        else:
            qos = QOS.AtLeastOnce
        topic = f"{self.atn_g_node_alias}/{payload.TypeAlias}"
        if self.settings.logging.verbose() or self.settings.logging.message_summary_enabled():
            self.logger.info(MessageSummary.format("OUT", self.atn_g_node_alias,
                             gw_mqtt_topic_encode(topic), payload, broker_flag="*"))
        self.gw_client.publish(
            topic=gw_mqtt_topic_encode(topic),
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

    def start_mqtt(self):
        self.gw_client.connect(self.settings.gridworks_mqtt.host, port=self.settings.gridworks_mqtt.port)
        self.gw_client.loop_start()

    def stop_mqtt(self):
        self.gw_client.disconnect()
        self.gw_client.loop_stop()

    def start(self):
        self.start_mqtt()
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()
        self.screen_print(f"Started {self.__class__}")

    def stop(self):
        self.screen_print("Stopping ...")
        self.terminate_main_loop()
        self.stop_mqtt()
        self.main_thread.join()
        self.screen_print("Stopped")

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
