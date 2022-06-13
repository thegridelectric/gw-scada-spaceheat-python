import uuid
from abc import ABC, abstractmethod
from typing import List

import helpers
import paho.mqtt.client as mqtt
import settings
from actors.utils import QOS, Subscription
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gs.gs_dispatch_maker import GsDispatch


class Atn_Base(ABC):
    def __init__(self, node: ShNode):
        self.node = node
        self.logging_on = False
        self.gwMqttBroker = settings.GW_MQTT_BROKER_ADDRESS
        self.gw_publish_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.gw_publish_client = mqtt.Client(self.gw_publish_client_id)
        self.gw_publish_client.username_pw_set(username=settings.GW_MQTT_USER_NAME,
                                               password=helpers.get_secret('GW_MQTT_PW'))
        self.gw_publish_client.connect(self.gwMqttBroker)
        self.gw_publish_client.loop_start()
        if self.logging_on:
            self.gw_publish_client.on_log = self.on_log
        self.gw_consume_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.gw_consume_client = mqtt.Client(self.gw_consume_client_id)
        self.gw_consume_client.username_pw_set(username=settings.GW_MQTT_USER_NAME,
                                               password=helpers.get_secret('GW_MQTT_PW'))
        self.gw_consume_client.connect(self.gwMqttBroker)
        if self.logging_on:
            self.gw_consume_client.on_log = self.on_log
        self.gw_consume_client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.gw_subscriptions())))
        self.gw_consume_client.on_message = self.on_gw_message

    def gw_consume(self):
        self.gw_consume_client.loop_start()

    def on_log(self, client, userdata, level, buf):
        self.screen_print(f"log: {buf}")

    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{settings.SCADA_G_NODE_ALIAS}/{GsPwr_Maker.type_alias}', Qos=QOS.AtMostOnce)]

    def on_gw_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split('/')
        except IndexError:
            raise Exception("topic must be of format A/B")
        if not from_alias == settings.SCADA_G_NODE_ALIAS:
            raise Exception(f"alias {from_alias} not my AtomicTNode!")
        if type_alias == GsPwr_Maker.type_alias:
            payload = GsPwr_Maker.type_to_tuple(message.payload)
            self.gs_pwr_received(payload=payload, from_g_node_alias=settings.SCADA_G_NODE_ALIAS)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")

    @abstractmethod
    def gs_pwr_received(self, payload: GsPwr, from_node: ShNode):
        raise NotImplementedError

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)

    def gw_publish(self, payload: GsDispatch):
        if type(payload) in [GsPwr, GsDispatch]:
            qos = QOS.AtMostOnce
        else:
            qos = QOS.AtLeastOnce
        self.gw_publish_client.publish(
            topic=f'{settings.ATN_G_NODE_ALIAS}/{payload.TypeAlias}',
            payload=payload.as_type(),
            qos=qos.value,
            retain=False)