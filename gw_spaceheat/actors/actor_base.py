import uuid
from abc import ABC, abstractmethod
from typing import List

import helpers
import paho.mqtt.client as mqtt
import settings
from data_classes.sh_node import ShNode
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr import GsPwr
from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry
from schema.schema_switcher import SchemaMakerByAliasDict
from actors.utils import QOS, Subscription


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
        self.consume_client.on_message = self.on_mqtt_message

    def on_log(self, client, userdata, level, buf):
        self.screen_print(f"log: {buf}")

    def consume(self):
        self.consume_client.loop_start()

    @abstractmethod
    def subscriptions(self) -> List[Subscription]:
        raise NotImplementedError

    def on_mqtt_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split('/')
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias not in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        from_node = ShNode.by_alias[from_alias]
        if type_alias not in SchemaMakerByAliasDict.keys():
            raise Exception(f"Type {type_alias} not recognized. Should be in SchemaByAliasDict keys!")
        payload_as_tuple = SchemaMakerByAliasDict[type_alias].type_to_tuple(message.payload)
        self.on_message(from_node=from_node, payload=payload_as_tuple)

    @abstractmethod
    def on_message(self, from_node: ShNode, payload: GtTelemetry):
        raise NotImplementedError

    def publish(self, payload: GtTelemetry):
        if type(payload) in [GsPwr, GsDispatch]:
            qos = QOS.AtMostOnce
        else:
            qos = QOS.AtLeastOnce
        self.publish_client.publish(
            topic=f'{self.node.alias}/{payload.TypeAlias}',
            payload=payload.as_type(),
            qos=qos.value,
            retain=False)

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
