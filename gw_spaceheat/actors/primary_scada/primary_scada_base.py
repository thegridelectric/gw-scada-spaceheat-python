from abc import abstractmethod, abstractproperty
import paho.mqtt.client as mqtt
import json
import uuid
from typing import List
import settings
import helpers
import threading
from actors.actor_base import ActorBase
from data_classes.sh_node import ShNode
from actors.mqtt_utils import Subscription, QOS
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry, GtTelemetry_Maker
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.gs.gs_dispatch_maker import GsDispatch, GsDispatch_Maker

MY_G_NODE_ALIAS = 'dw1.isone.nh.orange.1.ta.scada'
MY_ATN_G_NODE_ALIAS = 'dw1.isone.nh.orange.1'


class PrimaryScadaBase(ActorBase):
    def __init__(self, node: ShNode):
        super(PrimaryScadaBase, self).__init__(node=node)
        self.gwMqttBroker = settings.GW_MQTT_BROKER_ADDRESS
        self.gw_publish_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.gw_publish_client = mqtt.Client(self.gw_publish_client_id)
        self.gw_publish_client.username_pw_set(username=settings.GW_MQTT_USER_NAME , password=helpers.get_secret('GW_MQTT_PW'))
        self.gw_publish_client.connect(self.gwMqttBroker)
        self.gw_publish_client.loop_start()
        if self.logging_on:
            self.gw_publish_client.on_log = self.on_log
        self.gw_consume_client_id = ('-').join(str(uuid.uuid4()).split('-')[:-1])
        self.gw_consume_client = mqtt.Client(self.gw_consume_client_id)
        self.gw_consume_client.username_pw_set(username=settings.GW_MQTT_USER_NAME , password=helpers.get_secret('GW_MQTT_PW'))
        self.gw_consume_client.connect(self.gwMqttBroker)
        if self.logging_on:
            self.gw_consume_client.on_log = self.on_log
        self.gw_consume_thread = threading.Thread(target=self.gw_consume)

    def subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'a.m/{GsPwr_Maker.type_alias}',Qos=QOS.AtMostOnce),
                Subscription(Topic=f'a.tank.out.flowmeter1/{GtTelemetry_Maker.type_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp0/{GtTelemetry_Maker.type_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp1/{GtTelemetry_Maker.type_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp2/{GtTelemetry_Maker.type_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp3/{GtTelemetry_Maker.type_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp4/{GtTelemetry_Maker.type_alias}',Qos=QOS.AtLeastOnce )]

    def on_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split('/')
        except:
            raise Exception(f"topic must be of format A/B")
        from_node = ShNode.by_alias[from_alias]
        if not from_alias in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        if type_alias == GsPwr_Maker.type_alias:
            payload = GsPwr_Maker.type_to_tuple(message.payload)
            self.gs_pwr_received(payload=payload, from_node=from_node )
        elif type_alias == GtTelemetry_Maker.type_alias:
            self.screen_print(f"Topic {message.topic}")
            payload = GtTelemetry_Maker.type_to_tuple(message.payload)
            self.gt_telemetry_received(payload=payload, from_node=from_node)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")

    @abstractmethod
    def gs_pwr_received(self, payload: GsPwr):
        raise NotImplementedError

    @abstractmethod
    def gt_telemetry_received(self, payload: GtTelemetry, from_node: ShNode):
        raise NotImplementedError

    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{MY_ATN_G_NODE_ALIAS}/{GsDispatch_Maker.type_alias}',Qos=QOS.AtMostOnce)]

    def on_gw_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split('/')
        except:
            raise Exception(f"topic must be of format A/B")
        if not from_alias == MY_ATN_G_NODE_ALIAS:
            raise Exception(f"alias {from_alias} not my AtomicTNode!")
        from_node = ShNode.by_alias[from_alias]
        if type_alias == GsDispatch_Maker.type_alias:
            payload = GsDispatch_Maker.type_to_tuple(message.payload)
            self.gs_dispatch_received(payload=payload, from_node=from_node)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")

    @abstractmethod
    def gs_dispatch_received(self, payload: GsDispatch, from_node: ShNode):
        raise NotImplementedError

    def gw_consume(self):
        self.gw_consume_client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.gw_subscriptions())))
        self.gw_consume_client.on_message = self.on_gw_message
        self.gw_consume_client.loop_forever()

    def publish_gs_pwr(self, payload: GsPwr):
        topic = f'{MY_G_NODE_ALIAS}/{GsPwr_Maker.type_alias}'
        self.screen_print(f"Trying to publish {payload.as_type()} to topic {topic} on gw broker")
        self.gw_publish_client.publish(
            topic=topic,
            payload=payload.as_type(),
            qos = QOS.AtMostOnce.value,
            retain=False)

    @abstractproperty
    def my_meter(self) ->ShNode:
        raise NotImplementedError



    