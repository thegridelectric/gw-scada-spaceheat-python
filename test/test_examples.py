import time
import typing
from collections import defaultdict

import load_house
import schema.property_format
import settings
from actors.atn import Atn
from actors.boolean_actuator import BooleanActuator
from actors.cloud_ear import CloudEar
from actors.power_meter import PowerMeter
from actors.scada import Scada
from actors.simple_sensor import SimpleSensor
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response_maker import GtShCliScadaResponse
from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status import GtShSimpleSingleStatus
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import GtShSimpleStatus

LOCAL_MQTT_MESSAGE_DELTA_S = settings.LOCAL_MQTT_MESSAGE_DELTA_S
GW_MQTT_MESSAGE_DELTA = settings.GW_MQTT_MESSAGE_DELTA


class AtnRecorder(Atn):
    cli_resp_received: int

    def __init__(self, node: ShNode):
        self.cli_resp_received = 0
        self.latest_cli_response_payload: typing.Optional[GtShCliScadaResponse] = None
        super().__init__(node)

    def on_gw_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShCliScadaResponse):
            self.cli_resp_received += 1
            self.latest_cli_response_payload = payload
        super().on_gw_message(from_node, payload)


class EarRecorder(CloudEar):
    num_received: int
    num_received_by_topic: typing.Dict[str, int]

    def __init__(self):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        self.latest_payload = None
        super().__init__()

    def on_gw_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_message(self, from_node: ShNode, payload):
        self.latest_payload = payload
        super().on_gw_message(from_node, payload)


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
    load_house.load_all(input_json_file="input_data/houses.json")
    all_nodes = list(ShNode.by_alias.values())
    assert len(all_nodes) == 24
    aliases = list(ShNode.by_alias.keys())
    for i in range(len(aliases)):
        alias = aliases[i]
        node = ShNode.by_alias[alias]
        print(node)
    nodes_w_components = list(
        filter(lambda x: x.component_id is not None, ShNode.by_alias.values())
    )
    assert len(nodes_w_components) == 19
    actor_nodes_w_components = list(filter(lambda x: x.has_actor, nodes_w_components))
    assert len(actor_nodes_w_components) == 12
    tank_water_temp_sensor_nodes = list(
        filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes)
    )
    assert len(tank_water_temp_sensor_nodes) == 5
    for node in tank_water_temp_sensor_nodes:
        assert node.reporting_sample_period_s is not None


"""
def test_atn_cli():
    load_house.load_all(input_json_file="input_data/houses.json")

    elt = BooleanActuator(ShNode.by_alias["a.elt1.relay"])
    elt.start()
    elt.terminate_main_loop()
    scada = ScadaRecorder(node=ShNode.by_alias["a.s"])
    scada.start()
    scada.terminate_main_loop()
    atn = AtnRecorder(node=ShNode.by_alias["a"])
    atn.start()
    atn.terminate_main_loop()

    assert atn.cli_resp_received == 0
    atn.turn_off(ShNode.by_alias["a.elt1.relay"])
    time.sleep(2)

    atn.status()
    time.sleep(1)
    snapshot = atn.latest_cli_response_payload.Snapshot
    assert "a.elt1.relay" in snapshot.AboutNodeList
    assert TelemetryName.RELAY_STATE in snapshot.TelemetryNameList
    assert len(snapshot.ValueList) > 0
    idx = snapshot.AboutNodeList.index("a.elt1.relay")
    assert snapshot.ValueList[idx] == 0

    atn.turn_on(ShNode.by_alias["a.elt1.relay"])
    time.sleep(2)

    atn.status()
    time.sleep(1)

    snapshot = atn.latest_cli_response_payload.Snapshot
    idx = snapshot.AboutNodeList.index("a.elt1.relay")
    assert snapshot.ValueList[idx] == 1


def test_temp_sensor_loop_time():
    load_house.load_all(input_json_file="input_data/houses.json")
    all_nodes = list(ShNode.by_alias.values())
    tank_water_temp_sensor_nodes = list(
        filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes)
    )
    for node in tank_water_temp_sensor_nodes:
        sensor = SimpleSensor(node)
        start = time.time()
        sensor.check_and_report_temp()
        end = time.time()
        loop_ms = 1000 * (end - start)
        assert loop_ms > 200
    time.sleep(2)
"""


def test_async_power_metering_dag():
    """Verify power report makes it from meter -> Scada -> AtomicTNode"""
    load_house.load_all(input_json_file="input_data/houses.json")
    meter_node = ShNode.by_alias["a.m"]
    scada_node = ShNode.by_alias["a.s"]
    atn_node = ShNode.by_alias["a"]
    atn = Atn(node=atn_node)
    atn.start()
    atn.terminate_main_loop()
    atn.main_thread.join()
    assert atn.total_power_w == 0
    meter = PowerMeter(node=meter_node)
    meter.start()
    meter.terminate_main_loop()
    meter.main_thread.join()
    scada = Scada(node=scada_node)
    scada.start()
    scada.terminate_main_loop()
    scada.main_thread.join()
    meter.total_power_w = 2100
    payload = GsPwr_Maker(power=meter.total_power_w).tuple
    meter.publish(payload=payload)
    time.sleep(LOCAL_MQTT_MESSAGE_DELTA_S + GW_MQTT_MESSAGE_DELTA)
    time.sleep(0.3)
    assert atn.total_power_w == 2100


def test_scada_sends_status():
    load_house.load_all(input_json_file="input_data/houses.json")
    scada = ScadaRecorder(node=ShNode.by_alias["a.s"])
    scada.start()
    scada.terminate_main_loop()
    scada.main_thread.join()
    ear = EarRecorder()
    ear.start()
    ear.terminate_main_loop()
    ear.main_thread.join()
    time.sleep(2)
    thermo0_node = ShNode.by_alias["a.tank.temp0"]
    thermo1_node = ShNode.by_alias["a.tank.temp1"]

    thermo0 = SimpleSensor(node=thermo0_node)
    thermo0.start()
    thermo1 = SimpleSensor(node=thermo1_node)
    thermo1.start()
    time.sleep(1)
    time.sleep(thermo0.node.reporting_sample_period_s)
    thermo0.terminate_main_loop()
    thermo0.main_thread.join()
    thermo1.terminate_main_loop()
    thermo1.main_thread.join()

    assert scada.num_received_by_topic["a.tank.temp0/gt.telemetry.110"] > 0
    assert scada.num_received_by_topic["a.tank.temp1/gt.telemetry.110"] > 0
    assert len(scada.recent_readings[thermo0_node]) > 0
    for unix_ms in scada.recent_reading_times_ms[thermo0_node]:
        assert schema.property_format.is_reasonable_unix_time_ms(unix_ms)

    single_status = scada.make_single_status(thermo0_node)
    assert isinstance(single_status, GtShSimpleSingleStatus)
    assert single_status.TelemetryName == scada.config[thermo0_node].reporting.TelemetryName
    assert single_status.ReadTimeUnixMsList == scada.recent_reading_times_ms[thermo0_node]
    assert single_status.ValueList == scada.recent_readings[thermo0_node]
    assert single_status.ShNodeAlias == thermo0_node.alias

    scada.send_status()
    time.sleep(1)
    assert ear.num_received > 0
    scada_g_node_alias = f"{settings.ATN_G_NODE_ALIAS}.ta.scada"
    assert ear.num_received_by_topic[f"{scada_g_node_alias}/gt.sh.simple.status.100"] == 1
    assert isinstance(ear.latest_payload, GtShSimpleStatus)
    assert len(ear.latest_payload.SimpleSingleStatusList) == 2
    single_status = ear.latest_payload.SimpleSingleStatusList[0]
    assert single_status.TelemetryName == TelemetryName.WATER_TEMP_F_TIMES1000
    assert ear.latest_payload.ReportingPeriodS == 300
