"""Test Scada actor"""

import time
import typing

import pytest

import load_house
from actors.scada import Scada, ScadaCmdDiagnostic
from config import ScadaSettings
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status import (
    GtShBooleanactuatorCmdStatus,
)
from schema.gt.gt_sh_multipurpose_telemetry_status.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from schema.gt.gt_sh_simple_telemetry_status.gt_sh_simple_telemetry_status import (
    GtShSimpleTelemetryStatus,
)
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import (
    GtShTelemetryFromMultipurposeSensor_Maker,
)
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local_maker import (
    GtDispatchBooleanLocal_Maker,
)


def test_scada_small():
    settings = ScadaSettings()
    load_house.load_all(settings.world_root_alias)
    with pytest.raises(Exception):
        Scada(node=ShNode.by_alias["a"], settings=settings)
    scada = Scada(node=ShNode.by_alias["a.s"], settings=settings)
    meter_node = ShNode.by_alias["a.m"]
    relay_node = ShNode.by_alias["a.elt1.relay"]
    temp_node = ShNode.by_alias["a.tank.temp0"]
    assert list(scada.recent_ba_cmds.keys()) == scada.my_boolean_actuators()
    assert list(scada.recent_ba_cmd_times_unix_ms.keys()) == scada.my_boolean_actuators()
    assert list(scada.latest_simple_value.keys()) == scada.my_simple_sensors()
    assert list(scada.recent_simple_values.keys()) == scada.my_simple_sensors()
    assert list(scada.recent_simple_read_times_unix_ms.keys()) == scada.my_simple_sensors()
    assert list(scada.latest_value_from_multipurpose_sensor.keys()) == scada.my_telemetry_tuples()
    assert list(scada.recent_values_from_multipurpose_sensor.keys()) == scada.my_telemetry_tuples()
    assert (
        list(scada.recent_read_times_unix_ms_from_multipurpose_sensor.keys())
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
        scada.on_message(from_node=meter_node, payload="garbage")

    # Test on_gw_message getting a payload it does not recognize

    res = scada.on_gw_message(payload="garbage")
    assert res == ScadaCmdDiagnostic.PAYLOAD_NOT_IMPLEMENTED

    #################################
    # Testing messages received locally
    #################################

    boost = ShNode.by_alias["a.elt1.relay"]
    payload = GsPwr_Maker(power=2100).tuple
    with pytest.raises(Exception):
        scada.on_message(from_node=boost, payload=payload)

    payload = GtDispatchBooleanLocal_Maker(
        send_time_unix_ms=int(time.time() * 1000),
        from_node_alias="a.home",
        about_node_alias="a.elt1.relay",
        relay_state=0,
    ).tuple
    with pytest.raises(Exception):
        scada.on_message(from_node=boost, payload=payload)
    # Testing gt_sh_telemetry_from_multipurpose_sensor_received

    payload = GtShTelemetryFromMultipurposeSensor_Maker(
        about_node_alias_list=["a.unknown"],
        scada_read_time_unix_ms=int(time.time() * 1000),
        value_list=[17000],
        telemetry_name_list=[TelemetryName.CURRENT_RMS_MICRO_AMPS],
    ).tuple

    # throws error if AboutNode is unknown
    with pytest.raises(Exception):
        scada.gt_sh_telemetry_from_multipurpose_sensor_received(
            from_node=meter_node, payload=payload
        )

    # Testing gt_driver_booleanactuator_cmd_record_received

    # throws error if it gets a GtDriverBooleanactuatorCmd from
    # a node that is NOT a boolean actuator

    with pytest.raises(Exception):
        scada.gt_driver_booleanactuator_cmd_record_received(meter_node, payload)

    elt_relay_node = ShNode.by_alias["a.elt1.relay"]

    # Throws error if the ShNodeAlias is not equal to the from_node.

    with pytest.raises(Exception):
        scada.gt_driver_booleanactuator_cmd_record_received(elt_relay_node, payload)

    payload = GtShTelemetryFromMultipurposeSensor_Maker(
        about_node_alias_list=["a.tank"],
        scada_read_time_unix_ms=int(time.time() * 1000),
        value_list=[17000],
        telemetry_name_list=[TelemetryName.CURRENT_RMS_MICRO_AMPS],
    ).tuple

    # throws error if it does not track the telemetry tuple. In this
    # example, the telemetry tuple would have the electric meter
    # as the sensor node, reading amps for a water tank

    with pytest.raises(Exception):
        scada.gt_sh_telemetry_from_multipurpose_sensor_received(
            from_node=meter_node, payload=payload
        )

    payload = GtTelemetry_Maker(
        scada_read_time_unix_ms=int(time.time() * 1000),
        value=67000,
        exponent=3,
        name=TelemetryName.WATER_TEMP_F_TIMES1000,
    ).tuple

    # throws error if it receives a GtTelemetry reading
    # from a sensor which is not in its simple sensor list
    # - for example, like the multipurpose electricity meter
    with pytest.raises(Exception):
        scada.gt_telemetry_received(from_node=meter_node, payload=payload)

    ###########################################
    # Testing making status messages
    ###########################################

    s = scada.make_simple_telemetry_status(node=typing.cast(ShNode, "garbage"))
    assert s is None

    scada.recent_simple_read_times_unix_ms[temp_node] = [int(time.time() * 1000)]
    scada.recent_simple_values[temp_node] = [63000]
    s = scada.make_simple_telemetry_status(temp_node)
    assert isinstance(s, GtShSimpleTelemetryStatus)

    tt = TelemetryTuple(
        AboutNode=ShNode.by_alias["a.elt1"],
        SensorNode=ShNode.by_alias["a.m"],
        TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
    )
    scada.recent_values_from_multipurpose_sensor[tt] = [72000]
    scada.recent_read_times_unix_ms_from_multipurpose_sensor[tt] = [int(time.time() * 1000)]
    s = scada.make_multipurpose_telemetry_status(tt=tt)
    assert isinstance(s, GtShMultipurposeTelemetryStatus)
    s = scada.make_multipurpose_telemetry_status(tt=typing.cast(TelemetryTuple, "garbage"))
    assert s is None

    scada.recent_ba_cmds[relay_node] = []
    scada.recent_ba_cmd_times_unix_ms[relay_node] = []

    # returns None if asked make boolean actuator status for
    # a node that is not a boolean actuator

    s = scada.make_booleanactuator_cmd_status(meter_node)
    assert s is None

    s = scada.make_booleanactuator_cmd_status(relay_node)
    assert s is None

    scada.recent_ba_cmds[relay_node] = [0]
    scada.recent_ba_cmd_times_unix_ms[relay_node] = [int(time.time() * 1000)]
    s = scada.make_booleanactuator_cmd_status(relay_node)
    assert isinstance(s, GtShBooleanactuatorCmdStatus)

    scada.send_status()

    ##################################
    # Testing actuation
    ##################################

    # test that turn_on and turn_off only work for boolean actuator nodes

    result = scada.turn_on(meter_node)
    assert result == ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
    result = scada.turn_off(meter_node)
    assert result == ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR

    #################################
    # Other SCADA small tests
    ##################################

    scada._last_5_cron_s = int(time.time() - 400)
    assert scada.time_for_5_cron() is True
