import json
import os
import time
import typing
from collections import defaultdict

import load_house
import pytest
import schema.property_format
import settings
from actors.atn import Atn
from actors.boolean_actuator import BooleanActuator
from actors.cloud_ear import CloudEar
from actors.power_meter import PowerMeter
from actors.scada import Scada, ScadaCmdDiagnostic
from actors.simple_sensor import SimpleSensor
from command_line_utils import run_nodes_main
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.role.role_map import Role
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from schema.gs.gs_dispatch import GsDispatch
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response_maker import GtShCliScadaResponse
from schema.gt.gt_sh_node.gt_sh_node_maker import GtShNode_Maker
from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status import GtShSimpleSingleStatus
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import GtShSimpleStatus
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import (
    GtShTelemetryFromMultipurposeSensor_Maker,
)
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker

from utils import wait_for

LOCAL_MQTT_MESSAGE_DELTA_S = settings.LOCAL_MQTT_MESSAGE_DELTA_S
GW_MQTT_MESSAGE_DELTA = settings.GW_MQTT_MESSAGE_DELTA


class AtnRecorder(Atn):
    cli_resp_received: int
    latest_cli_response_payload: typing.Optional[GtShCliScadaResponse]

    def __init__(self, node: ShNode, logging_on: bool = False):
        self.cli_resp_received = 0
        self.latest_cli_response_payload: typing.Optional[GtShCliScadaResponse] = None
        super().__init__(node, logging_on=logging_on)

    def on_gw_message(self, from_node: ShNode, payload):
        if isinstance(payload, GtShCliScadaResponse):
            self.cli_resp_received += 1
            self.latest_cli_response_payload = payload
        super().on_gw_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        return (
            f"AtnRecorder [{self.node.alias}] cli_resp_received: {self.cli_resp_received}  "
            f"latest_cli_response_payload: {self.latest_cli_response_payload}"
        )


class EarRecorder(CloudEar):
    num_received: int
    num_received_by_topic: typing.Dict[str, int]
    latest_payload: typing.Optional[typing.Any]

    def __init__(self, logging_on: bool = False):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        self.latest_payload = None
        super().__init__(out_stub=None, logging_on=logging_on)

    def on_gw_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_gw_mqtt_message(client, userdata, message)

    def on_gw_message(self, from_node: ShNode, payload):
        self.latest_payload = payload
        super().on_gw_message(from_node, payload)

    def summary_str(self):
        """Summarize results in a string"""
        s = f"EarRecorder  num_received: {self.num_received}  latest_payload: {self.latest_payload}"
        for topic in sorted(self.num_received_by_topic):
            s += f"\n\t{self.num_received_by_topic[topic]:3d}: [{topic}]"
        return s


class ScadaRecorder(Scada):
    """Record data about a PrimaryScada execution during test"""

    num_received: int
    num_received_by_topic: typing.Dict[str, int]

    def __init__(self, node: ShNode, logging_on: bool = False):
        self.num_received = 0
        self.num_received_by_topic = defaultdict(int)
        super().__init__(node, logging_on=logging_on)

    def on_mqtt_message(self, client, userdata, message):
        self.num_received += 1
        self.num_received_by_topic[message.topic] += 1
        super().on_mqtt_message(client, userdata, message)

    def gs_dispatch_received(self, from_node: ShNode, payload: GsDispatch):
        pass

    def summary_str(self):
        """Summarize results in a string"""
        s = f"ScadaRecorder  {self.node.alias}  num_received: {self.num_received}"
        for topic in sorted(self.num_received_by_topic):
            s += f"\n\t{self.num_received_by_topic[topic]:3d}: [{topic}]"
        return s


def test_imports():
    """Verify modules can be imported"""
    # note: disable warnings about local imports
    import actors.strategy_switcher
    import load_house

    load_house.stickler()
    actors.strategy_switcher.stickler()


def test_load_real_house():
    real_atn_g_node_alias = "w.isone.nh.orange.1"
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(
        os.path.join(current_dir, "../gw_spaceheat/input_data/houses.json"), "r"
    ) as read_file:
        input_data = json.load(read_file)
    house_data = input_data[real_atn_g_node_alias]
    for d in house_data["ShNodes"]:
        GtShNode_Maker.dict_to_tuple(d)
    for node in ShNode.by_alias.values():
        print(node.parent)


def test_load_house():
    """Verify that load_house() successfully loads test objects"""
    load_house.load_all()
    for node in ShNode.by_alias.values():
        print(node.parent)
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
    assert len(nodes_w_components) == 18
    actor_nodes_w_components = list(filter(lambda x: x.has_actor, nodes_w_components))
    assert len(actor_nodes_w_components) == 12
    tank_water_temp_sensor_nodes = list(
        filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes)
    )
    assert len(tank_water_temp_sensor_nodes) == 5
    for node in tank_water_temp_sensor_nodes:
        assert node.reporting_sample_period_s is not None


# This test seems to be very sensitive to timing. It sometimes works locally but often fails in CI.
# Changing time.sleep(1) to a wait_for() call failed (possibly because the wrong thing was waited on).
# Changing the times.sleep(1) to time.sleep(5) made it fail later in the test.
#
# Commenting out for now.
#
# def test_atn_cli():
#     load_house.load_all()
#
#     elt_node = ShNode.by_alias["a.elt1.relay"]
#     elt = BooleanActuator(elt_node)
#     scada = ScadaRecorder(node=ShNode.by_alias["a.s"])
#     atn = AtnRecorder(node=ShNode.by_alias["a"])
#
#     try:
#         elt.start()
#         scada.start()
#         atn.start()
#         assert atn.cli_resp_received == 0
#         atn.turn_off(ShNode.by_alias["a.elt1.relay"])
#         time.sleep(1)
#         atn.status()
#         wait_for(lambda: atn.cli_resp_received > 0, 10, f"cli_resp_received == 0 {atn.summary_str()}")
#         assert atn.cli_resp_received == 1
#         print(atn.latest_cli_response_payload)
#         print(atn.latest_cli_response_payload.Snapshot)
#         print(atn.latest_cli_response_payload.Snapshot.AboutNodeList)
#         snapshot = atn.latest_cli_response_payload.Snapshot
#         assert snapshot.AboutNodeList == ["a.elt1.relay"]
#         assert snapshot.TelemetryNameList == [TelemetryName.RELAY_STATE]
#         assert len(snapshot.ValueList) == 1
#         idx = snapshot.AboutNodeList.index("a.elt1.relay")
#         assert snapshot.ValueList[idx] == 0
#
#         atn.turn_on(ShNode.by_alias["a.elt1.relay"])
#         wait_for(lambda: int(elt.relay_state) == 1, 10, f"Relay state {elt.relay_state}")
#         atn.status()
#         wait_for(lambda: atn.cli_resp_received > 1, 10, f"cli_resp_received <= 1 {atn.summary_str()}")
#
#         snapshot = atn.latest_cli_response_payload.Snapshot
#         assert snapshot.ValueList == [1]
#     finally:
#         # noinspection PyBroadException
#         try:
#             elt.stop()
#             scada.stop()
#             atn.stop()
#         except:
#             pass

# Refactor this test once we have a simulated relay that can be dispatched with
# the GridWorks Simulated Boolean Actuator and sensed with the GridWorks Simulated Power meter.
# As it stands, appears to be sensitive to timing.
#
# def test_async_power_metering_dag():
#     """Verify power report makes it from meter -> Scada -> AtomicTNode"""
#     logging_on = False
#     load_house.load_all()
#     meter_node = ShNode.by_alias["a.m"]
#     scada_node = ShNode.by_alias["a.s"]
#     atn_node = ShNode.by_alias["a"]
#     atn = AtnRecorder(node=atn_node, logging_on=logging_on)
#     meter = PowerMeter(node=meter_node)
#     scada = Scada(node=scada_node)
#     try:
#         atn.start()
#         atn.terminate_main_loop()
#         atn.main_thread.join()
#         assert atn.total_power_w == 0
#         meter.start()
#         meter.terminate_main_loop()
#         meter.main_thread.join()
#         scada.start()
#         scada.terminate_main_loop()
#         scada.main_thread.join()
#         meter.total_power_w = 2100
#         payload = GsPwr_Maker(power=meter.total_power_w).tuple
#         meter.publish(payload=payload)
#         wait_for(
#             lambda: atn.total_power_w == 2100,
#             10,
#             f"Atn did not receive power message. atn.total_power_w:{atn.total_power_w}  {atn.summary_str()}",
#         )
#     finally:
#         # noinspection PyBroadException
#         try:
#             atn.stop()
#             meter.stop()
#             scada.stop()
#         except:
#             pass


def test_scada_sends_status():
    logging_on = False
    load_house.load_all()
    scada = ScadaRecorder(node=ShNode.by_alias["a.s"], logging_on=logging_on)
    ear = EarRecorder(logging_on=logging_on)
    thermo0_node = ShNode.by_alias["a.tank.temp0"]
    thermo0 = SimpleSensor(node=thermo0_node, logging_on=logging_on)
    try:

        scada.start()
        scada.terminate_main_loop()
        scada.main_thread.join()
        wait_for(scada.client.is_connected, 1)
        wait_for(scada.gw_client.is_connected, 1)
        ear.start()
        ear.terminate_main_loop()
        ear.main_thread.join()
        wait_for(ear.gw_client.is_connected, 1)

        thermo0.start()
        thermo0.terminate_main_loop()
        thermo0.main_thread.join()
        thermo0.update_telemetry_value()
        assert thermo0.telemetry_value is not None
        thermo0.report_telemetry()

        def _scada_received_telemetry() -> bool:
            return scada.num_received_by_topic["a.tank.temp0/gt.telemetry.110"] > 0

        wait_for(_scada_received_telemetry, 5)
        for unix_ms in scada.recent_simple_read_times_unix_ms[thermo0_node]:
            assert schema.property_format.is_reasonable_unix_time_ms(unix_ms)
        single_status = scada.make_single_status_for_simple(thermo0_node)
        assert isinstance(single_status, GtShSimpleSingleStatus)
        assert single_status.TelemetryName == scada.config[thermo0_node].reporting.TelemetryName
        assert (
            single_status.ReadTimeUnixMsList == scada.recent_simple_read_times_unix_ms[thermo0_node]
        )
        assert single_status.ValueList == scada.recent_simple_values[thermo0_node]
        assert single_status.ShNodeAlias == thermo0_node.alias

        scada.send_status()
        time.sleep(1)
        assert ear.num_received > 0
        scada_g_node_alias = f"{settings.ATN_G_NODE_ALIAS}.ta.scada"
        assert ear.num_received_by_topic[f"{scada_g_node_alias}/gt.sh.simple.status.100"] == 1
        assert isinstance(ear.latest_payload, GtShSimpleStatus)
        single_status_list = ear.latest_payload.SimpleSingleStatusList
        assert len(single_status_list) > 0
        node_alias_list = list(map(lambda x: x.ShNodeAlias, single_status_list))
        assert "a.tank.temp0" in node_alias_list
        thermo0_idx = node_alias_list.index("a.tank.temp0")
        telemetry_name_list = list(map(lambda x: x.TelemetryName, single_status_list))
        assert telemetry_name_list[thermo0_idx] == TelemetryName.WATER_TEMP_F_TIMES1000
        assert ear.latest_payload.ReportingPeriodS == 300
    finally:
        # noinspection PyBroadException
        try:
            scada.stop()
            ear.stop()
            thermo0.stop()
        except:
            pass


@pytest.mark.parametrize(
    "aliases",
    [
        ["a.elt1.relay"],
        ["a.s"],
        ["a"],
    ],
)
def test_run_nodes_main(aliases):
    """Test command_line_utils.run_nodes_main()"""
    dbg = dict(actors={})
    try:
        run_nodes_main(
            argv=["-n", *aliases],
            dbg=dbg,
        )
        assert len(dbg["actors"]) == len(aliases)
    finally:
        for actor in dbg["actors"].values():
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass


def test_run_local():
    """Test the "run_local" script semantics"""
    load_house.load_all()
    aliases = [
        node.alias
        for node in filter(lambda x: (x.role != Role.ATN and x.has_actor), ShNode.by_alias.values())
    ]
    test_run_nodes_main(aliases)


def test_simple_sensor_value_update():
    load_house.load_all()
    thermo0 = SimpleSensor(ShNode.by_alias["a.tank.temp0"])
    try:
        thermo0.start()
        thermo0.terminate_main_loop()
        thermo0.main_thread.join()
        thermo0.update_telemetry_value()
    finally:
        # noinspection PyBroadException
        try:
            thermo0.stop()
        except:
            pass


def test_message_exchange(tmp_path, monkeypatch):
    """Run various nodes and verify they send each other messages as expected"""
    monkeypatch.chdir(tmp_path)
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)
    load_house.load_all()
    scada = ScadaRecorder(node=ShNode.by_alias["a.s"], logging_on=True)
    atn = AtnRecorder(node=ShNode.by_alias["a"], logging_on=True)
    ear = EarRecorder(logging_on=True)
    elt_relay = BooleanActuator(ShNode.by_alias["a.elt1.relay"], logging_on=True)
    meter = PowerMeter(node=ShNode.by_alias["a.m"], logging_on=True)
    thermo = SimpleSensor(node=ShNode.by_alias["a.tank.temp0"], logging_on=True)
    actors = [scada, atn, ear, elt_relay, meter, thermo]

    try:
        for actor in actors:
            actor.start()
        for actor in actors:
            if hasattr(actor, "client"):
                wait_for(
                    actor.client.is_connected,
                    1,
                    tag=f"ERROR waiting for {actor.node.alias} client connect",
                )
            if hasattr(actor, "qw_client"):
                wait_for(
                    actor.gw_client.is_connected,
                    1,
                    f"ERROR waiting for {actor.node.alias} gw_client connect",
                )
        atn.turn_on(ShNode.by_alias["a.elt1.relay"])
        wait_for(lambda: elt_relay.relay_state == 1, 10, f"Relay state {elt_relay.relay_state}")
        atn.status()
        wait_for(
            lambda: atn.cli_resp_received > 0, 10, f"cli_resp_received == 0 {atn.summary_str()}"
        )
        wait_for(
            lambda: len(ear.num_received_by_topic) > 0, 10, f"ear receipt. {ear.summary_str()}"
        )
        wait_for(
            lambda: scada.num_received_by_topic["a.elt1.relay/gt.telemetry.110"] > 0,
            10,
            f"scada elt telemetry. {scada.summary_str()}",
        )

        # wait_for(lambda: scada.num_received_by_topic["a.m/p"] > 0, 10, f"scada power. {scada.summary_str()}")
        # This should report after turning on the relay. But that'll take a simulated element
        # that actually turns on and can be read by the simulated power meter

        wait_for(
            lambda: scada.num_received_by_topic["a.tank.temp0/gt.telemetry.110"] > 0,
            10,
            f"scada temperature. {scada.summary_str()}",
        )

        atn.turn_off(ShNode.by_alias["a.elt1.relay"])
        wait_for(lambda: int(elt_relay.relay_state) == 0, 10, f"Relay state {elt_relay.relay_state}")

    finally:
        for actor in actors:
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass

###################
# Small Tests
####################

####################
# Scada small tests
###################


def test_scada_small():
    load_house.load_all()
    scada = Scada(node=ShNode.by_alias["a.s"])
    meter_node = ShNode.by_alias["a.m"]
    assert list(scada.latest_simple_value.keys()) == scada.my_simple_sensors()
    assert list(scada.recent_simple_values.keys()) == scada.my_simple_sensors()
    assert list(scada.recent_simple_read_times_unix_ms.keys()) == scada.my_simple_sensors()
    assert list(scada.latest_value_from_multifunction_sensor.keys()) == scada.my_telemetry_tuples()
    assert list(scada.recent_values_from_multifunction_sensor.keys()) == scada.my_telemetry_tuples()
    assert (
        list(scada.recent_read_times_unix_ms_from_multifunction_sensor.keys())
        == scada.my_telemetry_tuples()
    )

    local_topics = list(map(lambda x: x.Topic, scada.subscriptions()))
    multipurpose_topic_list = list(
        map(
            lambda x: f"{x.alias}/{GtShTelemetryFromMultipurposeSensor_Maker.type_alias}",
            scada.my_multipurpose_sensors(),
        )
    )
    assert set(multipurpose_topic_list) <= set(local_topics)
    simple_sensor_topic_list = list(
        map(lambda x: f"{x.alias}/{GtTelemetry_Maker.type_alias}", scada.my_simple_sensors())
    )
    assert set(simple_sensor_topic_list) <= set(local_topics)

    # Test on_message raises exception if it gets a payload that it does not recognize.
    # All of these messages will come via local broker by actors in the SCADA code
    # and so we have control over what they are.

    with pytest.raises(Exception):
        scada.on_message(from_node=meter_node, payload='garbage')

    # Test on_gw_message getting a payload it does not recognize

    res = scada.on_gw_message(payload='garbage')
    assert res == ScadaCmdDiagnostic.PAYLOAD_NOT_IMPLEMENTED

    with pytest.raises(Exception):
        boost = ShNode.by_alias['a.elt1.relay']
        payload = GsPwr_Maker(power=2100)
        scada.gs_pwr_received(from_node=boost, payload=payload)

    s = scada.make_single_status_for_simple(node='garbage')
    assert s is None

    tt = TelemetryTuple(
        AboutNode=ShNode.by_alias["a.elt1"],
        SensorNode=ShNode.by_alias["a.m"],
        TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
    )
    scada.recent_values_from_multifunction_sensor[tt] = [72000]
    scada.recent_read_times_unix_ms_from_multifunction_sensor[tt] = [int(time.time() * 1000)]
    s = scada.make_single_status_for_multipurpose(tt=tt)
    assert isinstance(s, GtShSimpleSingleStatus)
    s = scada.make_single_status_for_multipurpose(tt='garbage')
    assert s is None

    scada._last_5_cron_s = int(time.time() - 400)
    assert scada.time_for_5_cron() is True

    payload = GtShTelemetryFromMultipurposeSensor_Maker(
        about_node_alias_list=['a.unknown'],
        scada_read_time_unix_ms=int(time.time() * 1000),
        value_list=[17000],
        telemetry_name_list=[TelemetryName.CURRENT_RMS_MICRO_AMPS]
    )

    # throws error if AboutNode is unknown
    with pytest.raises(Exception):
        scada.gt_sh_telemetry_from_multipurpose_sensor_received(
            from_node=meter_node,
            payload=payload
        )

    payload = GtShTelemetryFromMultipurposeSensor_Maker(
        about_node_alias_list=['a.tank'],
        scada_read_time_unix_ms=int(time.time() * 1000),
        value_list=[17000],
        telemetry_name_list=[TelemetryName.CURRENT_RMS_MICRO_AMPS]
    )

    # throws error if it does not track the telemetry tuple. In this
    # example, the telemetry tuple would have the electric meter
    # as the sensor node, reading amps for a water tank
    with pytest.raises(Exception):
        scada.gt_sh_telemetry_from_multipurpose_sensor_received(
            from_node=meter_node,
            payload=payload
        )

    payload = GtTelemetry_Maker(
        scada_read_time_unix_ms=int(time.time() * 1000),
        value=67000,
        exponent=3,
        name=TelemetryName.WATER_TEMP_F_TIMES1000
    )

    # throws error if it receives a GtTelemetry reading
    # from a sensor which is not in its simple sensor list
    # - for example, like the multipurpose electricity meter
    with pytest.raises(Exception):
        scada.gt_telemetry_received(
            from_node=meter_node,
            payload=payload
        )

###################
# PowerMeter small tests
###################


def test_power_meter_small():
    load_house.load_all()
    meter = PowerMeter(node=ShNode.by_alias["a.m"])

    assert list(meter.max_telemetry_value.keys()) == meter.my_telemetry_tuples()
    assert list(meter.prev_telemetry_value.keys()) == meter.my_telemetry_tuples()
    assert list(meter.latest_telemetry_value.keys()) == meter.my_telemetry_tuples()
    assert list(meter.eq_config.keys()) == meter.my_telemetry_tuples()
    assert list(meter._last_sampled_s.keys()) == meter.my_telemetry_tuples()

    all_eq_configs = meter.config.reporting.ElectricalQuantityReportingConfigList
    amp_list = list(
        filter(
            lambda x: x.TelemetryName == TelemetryName.CURRENT_RMS_MICRO_AMPS
            and x.ShNodeAlias == "a.elt1",
            all_eq_configs,
        )
    )
    assert (len(amp_list)) == 1
    tt = TelemetryTuple(
        AboutNode=ShNode.by_alias["a.elt1"],
        SensorNode=meter.node,
        TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
    )
    assert tt in meter.my_telemetry_tuples()
    assert meter.latest_telemetry_value[tt] is None
    assert meter.prev_telemetry_value[tt] is None
    meter.update_prev_and_latest_value_dicts()
    assert isinstance(meter.latest_telemetry_value[tt], int)
    meter.update_prev_and_latest_value_dicts()
    assert isinstance(meter.prev_telemetry_value[tt], int)

    assert meter.max_telemetry_value[tt] == 10**7
    meter.prev_telemetry_value[tt] = meter.latest_telemetry_value[tt]
    assert meter.value_exceeds_async_threshold(tt) is False
    meter.latest_telemetry_value[tt] += int(
        0.1 * meter.eq_config[tt].AsyncReportThreshold * meter.max_telemetry_value[tt]
    )
    assert meter.value_exceeds_async_threshold(tt) is False
    assert meter.should_report_telemetry_reading(tt)
    meter.report_sampled_telemetry_values([tt])
    assert meter.should_report_telemetry_reading(tt) is False

    meter.latest_telemetry_value[tt] += int(
        meter.eq_config[tt].AsyncReportThreshold * meter.max_telemetry_value[tt]
    )
    assert meter.value_exceeds_async_threshold(tt) is True
