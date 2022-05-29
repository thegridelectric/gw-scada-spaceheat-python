from abc import abstractmethod, abstractproperty
import json
from typing import List
from actors.actor_base import ActorBase
from data_classes.sh_node import ShNode
from actors.mqtt_utils import Subscription, QOS
from schema.gt.gt_telemetry.gt_telemetry_1_0_1_maker import  GtTelemetry101_Maker, GtTelemetry101
from schema.gs.gs_pwr_1_0_0_maker import GsPwr100_Maker, GsPwr100


class PrimaryScadaBase(ActorBase):
    def __init__(self, node: ShNode):
        super(PrimaryScadaBase, self).__init__(node=node)

    def subscriptions(self) -> List[Subscription]:
        return [Subscription(Topic=f'{self.my_meter.alias}/{GsPwr100_Maker.mp_alias}',Qos=QOS.AtMostOnce),
                Subscription(Topic=f'a.tank.out.flowmeter1/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce),
                Subscription(Topic=f'a.tank.temp0/{GtTelemetry101_Maker.mp_alias}',Qos=QOS.AtLeastOnce)]

    def on_message(self, client, userdata, message):
        try:
            (from_alias, mp_alias) = message.topic.split('/')
        except:
            raise Exception(f"topic must be of format A/B")
        if not from_alias in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        if mp_alias == GsPwr100_Maker.mp_alias:
            # self.raw_payload = message.payload
            payload = GsPwr100_Maker.binary_to_type(message.payload)
            self.gs_pwr_100_from_powermeter(payload)
        elif mp_alias == GtTelemetry101_Maker.mp_alias:
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

    def publish_gs_pwr(self, payload: GsPwr100):
        topic = f'{self.node.alias}/{GsPwr100_Maker.mp_alias}'
        self.publish_client.publish(
            topic=topic,
            payload=payload.asbinary(),
            qos = QOS.AtMostOnce.value,
            retain=False)
        self.screen_print(f"Just published {payload} to topic {topic}")

    @abstractproperty
    def my_meter(self) ->ShNode:
        raise NotImplementedError