# This should be an absolute import from package base: "gw_spaceheat...."
# That requires changes *all* imports to use absolute import, so we don't do this in this demo.
import time
import typing
from collections import defaultdict

from data_classes.cacs.temp_sensor_cac import TempSensorCac
from data_classes.sh_node import ShNode
import load_house
from actors.power_meter import PowerMeter
from actors.primary_scada import PrimaryScada
from actors.atn import Atn
from actors.tank_water_temp_sensor import TankWaterTempSensor
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr_Maker


class ScadaRecorder(PrimaryScada):
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
    print(ShNode.by_alias['a.s'])
    assert len(ShNode.by_alias) == 24
    nodes_w_components = list(filter(lambda x: x.primary_component_id is not None, ShNode.by_alias.values()))
    assert len(nodes_w_components) == 19
    actor_nodes_w_components = list(filter(lambda x: x.python_actor_name is not None, nodes_w_components))
    assert len(actor_nodes_w_components) == 7
    temp_sensor_nodes = list(filter(lambda x: isinstance(
        x.primary_component.cac, TempSensorCac), actor_nodes_w_components))
    assert len(temp_sensor_nodes) == 5


def test_async_power_metering_dag():
    load_house.load_all(house_json_file='../test/test_data/test_load_house.json')
    meter_node = ShNode.by_alias["a.m"]
    scada_node = ShNode.by_alias["a.s"]
    atn_node = ShNode.by_alias["a"]
    meter = PowerMeter(node=meter_node)
    meter.terminate_sensing()
    meter.sensing_thread.join()
    scada = PrimaryScada(node=scada_node)
    scada.terminate_scheduling()
    scada.schedule_thread.join()
    atn = Atn(node=atn_node)
    assert atn.total_power_w == 0
    meter.total_power_w = 2100
    payload = GsPwr_Maker(power=meter.total_power_w).tuple
    meter.publish(payload=payload)
    time.sleep(.3)
#     assert atn.total_power_w == 2100


def test_collect_temp_data():
    """Verify Scada receives publication from TankWaterTempSensor"""
    load_house.load_all(house_json_file='../test/test_data/test_load_house.json')
    scada = ScadaRecorder(node=typing.cast(ShNode, ShNode.by_alias["a.s"]))
    thermo = TankWaterTempSensor(node=typing.cast(ShNode, ShNode.by_alias["a.tank.temp0"]))
    time.sleep(1)
    thermo.terminate_sensing()
    thermo.sensing_thread.join()
    scada.terminate_scheduling()
    scada.schedule_thread.join()
    assert scada.num_received > 0
    assert scada.num_received_by_topic["a.tank.temp0/gt.telemetry.110"] == scada.num_received
