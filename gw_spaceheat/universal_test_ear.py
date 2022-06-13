from ast import Sub
from typing import List
import paho.mqtt.client as mqtt
import settings
import helpers
from data_classes.sh_node import ShNode
from actors.mqtt_utils import QOS, Subscription
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry, GtTelemetry_Maker
from schema.gs.gs_dispatch_maker import GsDispatch, GsDispatch_Maker
from schema.gs.gs_pwr_maker import GsPwr, GsPwr_Maker
from schema.schema_switcher import SchemaSwitcher


class UniversalTestEar():

    def __init__(self):
        self.alias = 'universal.test.ear'
        self.mqttBroker = settings.LOCAL_MQTT_BROKER_ADDRESS
        self.client = mqtt.Client(self.alias)
        self.client.username_pw_set(username=settings.LOCAL_MQTT_USER_NAME,
                                    password=helpers.get_secret('LOCAL_MQTT_PW'))
        self.client.connect(self.mqttBroker)
        self.client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.subscriptions())))
        self.client.on_message = self.on_message
        # self.gwMqttBroker = settings.GW_MQTT_BROKER_ADDRESS
        # self.gw_client = mqtt.Client(f'gw.{self.alias}')
        # self.gw_client.username_pw_set(username=settings.GW_MQTT_USER_NAME,
        #                                        password=helpers.get_secret('GW_MQTT_PW'))
        # self.gw_client.connect(self.gwMqttBroker)
        # self.gw_client.subscribe(list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.gw_subscriptions())))
        # self.gw_client.on_message = self.on_gw_message
        self.latest_from_node: ShNode = None
        self.latest_payload: GtTelemetry = None

    def subscriptions(self) -> List[Subscription]:
        local_aliases = set(ShNode.by_alias.keys()) - {'a'}
        subscriptions = []
        for alias in local_aliases:
            subscriptions.append(Subscription(Topic=f'{alias}/#', Qos=QOS.AtLeastOnce))
        subscriptions.append(Subscription(Topic='a.tank.temp0/gt.telemetry.110', Qos=QOS.AtLeastOnce))
        return subscriptions

    def gw_subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{settings.SCADA_G_NODE_ALIAS}/#', Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'{settings.ATN_G_NODE_ALIAS}/#', Qos=QOS.AtLeastOnce)]

    def on_message(self, client, userdata, message):
        print(f"Got message {message.payload} with topic {message.topic}")
        try:
            (from_alias, type_alias) = message.topic.split('/')
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias not in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        self.latest_from_node = ShNode.by_alias[from_alias]
        if type_alias not in SchemaSwitcher.keys():
            raise Exception(f"Unrecognized type {type_alias}. Needs to be a key in SchemaSwitcher!")
        self.latest_payload = SchemaSwitcher[type_alias].type_to_tuple(message.payload)

    def on_gw_message(self, client, userdata, message):
        try:
            (from_alias, type_alias) = message.topic.split('/')
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias == settings.ATN_G_NODE_ALIAS:
            if 'a' not in ShNode.by_alias.keys():
                raise Exception("alias 'a' not in ShNode.by_alias keys!")
            self.latest_from_node = ShNode.by_alias['a']
        elif from_alias == settings.SCADA_G_NODE_ALIAS:
            if 'a.s' not in ShNode.by_alias.keys():
                raise Exception("alias 'a.s' not in ShNode.by_alias keys!")
            self.latest_from_node = ShNode.by_alias['a.s']
        elif from_alias not in [settings.ATN_G_NODE_ALIAS, settings.SCADA_G_NODE_ALIAS]:
            raise Exception(f"alias {from_alias} not in {[settings.ATN_G_NODE_ALIAS, settings.SCADA_G_NODE_ALIAS]}!")

        if type_alias == GsDispatch.TypeAlias:
            self.latest_payload = GsDispatch_Maker.type_to_tuple(message.payload)
        elif type_alias == GsPwr.TypeAlias:
            self.latest_payload = GsPwr_Maker.type_to_tuple(message.payload)
