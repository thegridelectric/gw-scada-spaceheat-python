import csv
import json
import os
import threading
import typing
import uuid
from abc import ABC, abstractmethod
from functools import cached_property
from typing import List

import paho.mqtt.client as mqtt

import helpers
from config import ScadaSettings
from actors.utils import QOS, Subscription
from data_classes.sh_node import ShNode
from data_classes.components.electric_meter_component import ElectricMeterComponent
from drivers.power_meter.power_meter_driver import PowerMeterDriver
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import (
    GridworksSimPm1_PowerMeterDriver,
)
from drivers.power_meter.schneiderelectric_iem3455__power_meter_driver import (
    SchneiderElectricIem3455_PowerMeterDriver,
)
from drivers.power_meter.unknown_power_meter_driver import UnknownPowerMeterDriver
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.make_model.make_model_map import MakeModel
from schema.enums.role.role_map import Role
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr import GsPwr
from schema.schema_switcher import TypeMakerByAliasDict


class ActorBase(ABC):
    @classmethod
    def all_power_tuples(cls) -> List[TelemetryTuple]:
        telemetry_tuples = []
        for node in cls.all_metered_nodes():
            telemetry_tuples += [
                TelemetryTuple(
                    AboutNode=node,
                    SensorNode=cls.power_meter_node(),
                    TelemetryName=TelemetryName.POWER_W,
                )
            ]
        return telemetry_tuples

    @classmethod
    def all_power_meter_telemetry_tuples(cls) -> List[TelemetryTuple]:
        telemetry_tuples = cls.all_power_tuples()
        for about_node in cls.all_metered_nodes():
            for telemetry_name in cls.power_meter_driver().additional_telemetry_name_list():
                telemetry_tuples.append(
                    TelemetryTuple(
                        AboutNode=about_node,
                        SensorNode=cls.power_meter_node(),
                        TelemetryName=telemetry_name,
                    )
                )

        return telemetry_tuples

    @classmethod
    def all_metered_nodes(cls) -> List[ShNode]:
        """All nodes whose power level is metered and included in power reporting by the Scada"""
        return cls.all_resistive_heaters()

    @classmethod
    def all_resistive_heaters(cls) -> List[ShNode]:
        all_nodes = list(ShNode.by_alias.values())
        return list(filter(lambda x: (x.role == Role.BOOST_ELEMENT), all_nodes))

    @classmethod
    def power_meter_driver(cls) -> PowerMeterDriver:
        component: ElectricMeterComponent = typing.cast(ElectricMeterComponent, cls.power_meter_node().component)
        cac = component.cac
        if cac.make_model == MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            driver = UnknownPowerMeterDriver(component=component)
        elif cac.make_model == MakeModel.SCHNEIDERELECTRIC__IEM3455:
            driver = SchneiderElectricIem3455_PowerMeterDriver(component=component)
        elif cac.make_model == MakeModel.GRIDWORKS__SIMPM1:
            driver = GridworksSimPm1_PowerMeterDriver(component=component)
        else:
            raise NotImplementedError(f"No ElectricMeter driver yet for {cac.make_model}")
        return driver

    @classmethod
    def power_meter_node(cls) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role PowerMeter"""
        nodes = list(filter(lambda x: x.role == Role.POWER_METER, ShNode.by_alias.values()))
        return nodes[0]

    @classmethod
    def scada_node(cls) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role Scada"""
        nodes = list(filter(lambda x: x.role == Role.SCADA, ShNode.by_alias.values()))
        return nodes[0]

    @classmethod
    def home_alone_node(cls) -> ShNode:
        """Schema for input data enforces exactly one Spaceheat Node with role HomeAlone"""
        nodes = list(filter(lambda x: x.role == Role.HOME_ALONE, ShNode.by_alias.values()))
        return nodes[0]

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

    def __init__(self, node: ShNode, settings: ScadaSettings):
        self._main_loop_running = False
        self.main_thread = None
        self.node = node
        self.settings = settings
        self.log_csv = f"{self.settings.output_dir}/debug_logs/{self.node.alias}_{str(uuid.uuid4()).split('-')[1]}.csv"
        if self.settings.logging_on:
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
        if self.settings.logging_on:
            self.client.on_log = self.on_log
            self.client.enable_logger()

    def subscribe(self):
        subscriptions = list(map(lambda x: (f"{x.Topic}", x.Qos.value), self.subscriptions()))
        if subscriptions:
            self.client.subscribe(subscriptions)

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
            (from_alias, type_alias) = message.topic.split("/")
        except IndexError:
            raise Exception("topic must be of format A/B")
        if from_alias not in ShNode.by_alias.keys():
            raise Exception(f"alias {from_alias} not in ShNode.by_alias keys!")
        from_node = ShNode.by_alias[from_alias]
        if type_alias not in TypeMakerByAliasDict.keys():
            raise Exception(
                f"Type {type_alias} not recognized. Should be in TypeMakerByAliasDict keys!"
            )
        payload_as_tuple = TypeMakerByAliasDict[type_alias].type_to_tuple(message.payload)
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
        self.client.publish(
            topic=topic,
            payload=payload.as_type(),
            qos=qos.value,
            retain=False,
        )
        # self.screen_print(f"published to {topic}")

    def terminate_main_loop(self):
        self._main_loop_running = False

    def start(self):
        self.client.connect(self.settings.local_mqtt.host, port=self.settings.local_mqtt.port)
        self.client.loop_start()
        self.main_thread = threading.Thread(target=self.main)
        self.main_thread.start()
        self.screen_print(f"Started {self.__class__}")

    def stop(self):
        self.screen_print("Stopping ...")
        self.terminate_main_loop()
        self.client.disconnect()
        self.client.loop_stop()
        self.main_thread.join()
        self.screen_print("Stopped")

    @abstractmethod
    def main(self):
        raise NotImplementedError

    def screen_print(self, note):
        header = f"{self.node.alias}: "
        print(header + note)
