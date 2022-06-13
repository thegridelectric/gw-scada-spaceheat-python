# This should be an absolute import from package base: "gw_spaceheat...."
# That requires changes *all* imports to use absolute import, so we don't do this in this demo.
import time
from data_classes.cacs.temp_sensor_cac import TempSensorCac
from data_classes.sh_node import ShNode
import load_house
from actors.power_meter.power_meter import PowerMeter
from actors.primary_scada.primary_scada import PrimaryScada
from actors.atn.atn import Atn
from actors.sensor.tank_water_temp_sensor import TankWaterTempSensor
from universal_test_ear import UniversalTestEar
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry, GtTelemetry_Maker
from schema.gs.gs_pwr_maker import GsPwr_Maker
# noinspection PyUnresolvedReferences

LOCAL_MQTT_MESSAGE_DELTA_S = 0.05
GW_MQTT_MESSAGE_DELTA = 0.05

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


def test_temp_sensor_sends():
    load_house.load_all(house_json_file='../test/test_data/test_load_house.json')

    t0_node = ShNode.by_alias["a.tank.temp0"]
    t0 = TankWaterTempSensor(node=t0_node)
    t0.terminate_sensing()
    t0.sensing_thread.join()
    ear = UniversalTestEar()
    ear.client.loop_start()
    payload = GtTelemetry_Maker(name=t0.telemetry_name,
                                value=int(t0.temp),
                                exponent=0,
                                scada_read_time_unix_ms=int(time.time() * 1000)).tuple
    t0.publish(payload=payload)
    time.sleep(LOCAL_MQTT_MESSAGE_DELTA_S)
    assert isinstance(ear.latest_payload, GtTelemetry)
    assert ear.latest_from_node == t0_node


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
    atn.terminate_scheduling()
    atn.schedule_thread.join()
    assert atn.total_power_w == 0
    meter.total_power_w = 2100
    payload = GsPwr_Maker(power=meter.total_power_w).tuple
    meter.publish(payload=payload)
    time.sleep(LOCAL_MQTT_MESSAGE_DELTA_S + GW_MQTT_MESSAGE_DELTA)
    assert atn.total_power_w == 2100
