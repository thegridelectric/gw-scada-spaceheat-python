import time
import typing
from collections import defaultdict

import load_house
import settings
from actors.atn import Atn
from actors.power_meter import PowerMeter
from actors.scada import Scada
from actors.tank_water_temp_sensor import TankWaterTempSensor
from data_classes.sh_node import ShNode
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.enums.role.role_map import Role

LOCAL_MQTT_MESSAGE_DELTA_S = settings.LOCAL_MQTT_MESSAGE_DELTA_S
GW_MQTT_MESSAGE_DELTA = settings.GW_MQTT_MESSAGE_DELTA


class ScadaRecorder(Scada):
    """Record data about a PrimaryScada execution during test"""

    num_received: int
    num_received_by_topic: typing.Dict[str, int]

    def __init__(self, node: ShNode):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        super().__init__(node)

    def on_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_mqtt_message(client, userdata, message)


def test_imports():
    """Verify modules can be imported"""
    # note: disable warnings about local imports
    import actors.strategy_switcher
    import load_house
    load_house.stickler()
    actors.strategy_switcher.stickler()


def test_load_house():
    """Verify that load_house() successfully loads test objects"""
    assert len(ShNode.by_alias) == 0
    load_house.load_all(house_json_file='../test/test_data/test_load_house.json')
    all_nodes = list(ShNode.by_alias.values())
    assert len(all_nodes) == 24
    aliases = list(ShNode.by_alias.keys())
    for i in range(len(aliases)):
        alias = aliases[i]
        node = ShNode.by_alias[alias]
        print(node)
    nodes_w_components = list(filter(lambda x: x.component_id is not None, ShNode.by_alias.values()))
    assert len(nodes_w_components) == 19
    actor_nodes_w_components = list(filter(lambda x: x.has_actor, nodes_w_components))
    assert len(actor_nodes_w_components) == 7
    tank_water_temp_sensor_nodes = list(filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes))
    assert len(tank_water_temp_sensor_nodes) == 5


def test_async_power_metering_dag():
    """Verify power report makes it from meter -> Scada -> AtomicTNode"""
    load_house.load_all(house_json_file='../test/test_data/test_load_house.json')
    meter_node = ShNode.by_alias["a.m"]
    scada_node = ShNode.by_alias["a.s"]
    atn_node = ShNode.by_alias["a"]
    meter = PowerMeter(node=meter_node)
    meter.start()
    meter.terminate_main_loop()
    meter.main_thread.join()
    scada = Scada(node=scada_node)
    scada.start()
    scada.terminate_main_loop()
    scada.main_thread.join()
    atn = Atn(node=atn_node)
    atn.start()
    atn.terminate_main_loop()
    atn.main_thread.join()
    assert atn.total_power_w == 0
    meter.total_power_w = 2100
    payload = GsPwr_Maker(power=meter.total_power_w).tuple
    meter.publish(payload=payload)
    time.sleep(LOCAL_MQTT_MESSAGE_DELTA_S + GW_MQTT_MESSAGE_DELTA)
    time.sleep(.3)
    assert atn.total_power_w == 2100


def test_collect_temp_data():
    """Verify Scada receives publication from TankWaterTempSensor"""
    load_house.load_all(house_json_file='../test/test_data/test_load_house.json')
    scada = ScadaRecorder(node=typing.cast(ShNode, ShNode.by_alias["a.s"]))
    scada.start()
    thermo = TankWaterTempSensor(node=typing.cast(ShNode, ShNode.by_alias["a.tank.temp0"]))
    thermo.start()
    time.sleep(1)
    thermo.terminate_main_loop()
    thermo.main_thread.join()
    scada.terminate_main_loop()
    scada.main_thread.join()
    assert scada.num_received > 0
    assert scada.num_received_by_topic["a.tank.temp0/gt.telemetry.110"] == scada.num_received
