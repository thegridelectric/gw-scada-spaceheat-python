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
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import  GtTelemetry101_Maker, GtTelemetry101
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100
from schema.gs.gs_dispatch_1_0_0_maker import GsDispatch100_Maker, GsDispatch100

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
        return [Subscription(Topic=f'{self.my_meter.alias}/{GsPwr100_Maker.mp_alias}',Qos=QOS.AtMostOnce),
                Subscription(Topic=f'a.tank.out.flowmeter1/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp0/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp1/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp2/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp3/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp4/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce )]

    def on_message(self, client, userdata, message):
        try:
            (from_alias, mp_alias) = message.topic.split('/')
        except:
            raise Exception(f"topic must be of format A/B")
        if not from_alias in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        if mp_alias == GsPwr100_Maker.mp_alias:
            payload = GsPwr100_Maker.binary_to_type(message.payload)
            self.gs_pwr_100_from_powermeter(payload)
        elif mp_alias == GtTelemetry101_Maker.mp_alias:
            self.screen_print(f"Topic {message.topic}")
            payload = GtTelemetry101_Maker.camel_dict_to_type(json.loads(message.payload))
            from_node = ShNode.by_alias[from_alias]
            self.gt_telemetry_100_received(payload=payload, from_node=from_node)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")

    @abstractmethod
    def gs_pwr_100_from_powermeter(self, payload: GsPwr100):
        raise NotImplementedError

    @abstractmethod
    def gt_telemetry_100_received(self, payload: GtTelemetry101, from_node: ShNode):
        raise NotImplementedError

    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{MY_ATN_G_NODE_ALIAS}/{GsDispatch100_Maker.mp_alias}',Qos=QOS.AtMostOnce)]

    def on_gw_message(self, client, userdata, message):
        try:
            (from_alias, mp_alias) = message.topic.split('/')
        except:
            raise Exception(f"topic must be of format A/B")
        if not from_alias == MY_ATN_G_NODE_ALIAS:
            raise Exception(f"alias {from_alias} not my AtomicTNode!")
        if mp_alias == GsDispatch100_Maker.mp_alias:
            payload = GsDispatch100_Maker.binary_to_type(message.payload)
            from_node = ShNode.by_alias[from_alias]
            self.gs_dispatch_100_received(payload=payload, from_node=from_node)
        else:
            self.screen_print(f"{message.topic} subscription not implemented!")



    @abstractmethod
    def gs_dispatch_100_received(self, payload: GsDispatch100, from_node: ShNode):
        raise NotImplementedError

    def gw_consume(self):
        self.gw_consume_client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.gw_subscriptions())))
        self.gw_consume_client.on_message = self.on_gw_message
        self.gw_consume_client.loop_forever()

    def publish_gs_pwr_to_atn(self, payload: GsPwr100):
        topic = f'{MY_G_NODE_ALIAS}/{GsPwr100_Maker.mp_alias}'
        self.screen_print(f"Trying to publish {payload} to topic {topic} on gw broker")
        self.gw_publish_client.publish(
            topic=topic,
            payload=payload.asbinary(),
            qos = QOS.AtMostOnce.value,
            retain=False)

    @abstractproperty
    def my_meter(self) ->ShNode:
        raise NotImplementedError



    