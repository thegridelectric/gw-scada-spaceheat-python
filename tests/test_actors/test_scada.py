"""Test Scada actor"""
import time
import typing
from tests.utils.fragment_runner import FragmentRunner
from tests.utils.fragment_runner import ProtocolFragment
from tests.utils import wait_for

import load_house
import pytest
from actors.actor_base import ActorBase
from actors.scada import Scada
from actors.scada import ScadaCmdDiagnostic
from config import ScadaSettings
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from gwproto.enums import TelemetryName
from gwproto.messages import  GsPwr_Maker
from gwproto.messages import  GtDispatchBooleanLocal_Maker
from gwproto.messages import  GtShBooleanactuatorCmdStatus
from gwproto.messages import  GtShMultipurposeTelemetryStatus
from gwproto.messages import  GtShSimpleTelemetryStatus
from gwproto.messages import  GtShStatus
from gwproto.messages import  GtShTelemetryFromMultipurposeSensor_Maker
from gwproto.messages import  GtTelemetry_Maker
from gwproto.messages import  SnapshotSpaceheat


def test_scada_small():
    settings = ScadaSettings()
    layout = load_house.load_all(settings)
    with pytest.raises(Exception):
        Scada("a", settings=settings, hardware_layout=layout)
    scada = Scada("a.s", settings=settings, hardware_layout=layout)
    meter_node = layout.node("a.m")
    relay_node = layout.node("a.elt1.relay")
    temp_node = layout.node("a.tank.temp0")
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

    boost = layout.node("a.elt1.relay")
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

    elt_relay_node = layout.node("a.elt1.relay")

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
        AboutNode=layout.node("a.elt1"),
        SensorNode=layout.node("a.m"),
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


def test_scada_periodic_status_delivery():
    """Verify scada periodic status and snapshot"""

    class Fragment(ProtocolFragment):

        def __init__(self, runner_: FragmentRunner):
            runner_.actors.scada.last_5_cron_s = int(time.time())
            super().__init__(runner_)

        def get_requested_actors(self) -> typing.Sequence[ActorBase]:
            return [self.runner.actors.scada, self.runner.actors.atn]

        def run(self):
            scada = self.runner.actors.scada
            atn = self.runner.actors.atn
            assert atn.num_received_by_topic[scada.status_topic] == 0
            assert atn.num_received_by_topic[scada.snapshot_topic] == 0
            scada.last_5_cron_s -= 299
            wait_for(
                lambda: atn.num_received_by_topic[scada.status_topic] == 1,
                5,
                "Atn wait for status message"
            )
            wait_for(
                lambda: atn.num_received_by_topic[scada.snapshot_topic] == 1,
                5,
                "Atn wait for snapshot message"
            )

    FragmentRunner.run_fragment(Fragment)


def test_scada_snaphot_request_delivery():
    """Verify scada sends snapshot upon request from Atn"""

    class Fragment(ProtocolFragment):

        def get_requested_actors(self) -> typing.Sequence[ActorBase]:
            return [self.runner.actors.scada, self.runner.actors.atn]

        def run(self):
            scada = self.runner.actors.scada
            atn = self.runner.actors.atn
            assert atn.num_received_by_topic[scada.snapshot_topic] == 0
            atn.status()
            wait_for(
                lambda: atn.num_received_by_topic[scada.snapshot_topic] == 1,
                10,
                "Atn wait for snapshot message"
            )

    FragmentRunner.run_fragment(Fragment)


def test_scada_status_content_dynamics():
    """Verify Scada status contains command acks from BooleanActuators and telemetry from SimpleSensor and
    MultipurposeSensor."""
    class Fragment(ProtocolFragment):

        def __init__(self, runner_: FragmentRunner):
            runner_.actors.scada._scada_atn_fast_dispatch_contract_is_alive_stub = True
            runner_.actors.scada.last_5_cron_s = int(time.time())
            super().__init__(runner_)

        def get_requested_actors(self) -> typing.Sequence[ActorBase]:
            return [self.runner.actors.scada, self.runner.actors.atn]

        def run(self):
            atn = self.runner.actors.atn
            scada = self.runner.actors.scada
            relay = self.runner.actors.relay
            meter = self.runner.actors.meter
            thermo = self.runner.actors.thermo
            relay_telemetry_topic = f"{relay.node.alias}/gt.telemetry.110"
            relay_command_received_topic = f"{relay.node.alias}/gt.driver.booleanactuator.cmd.100"
            meter_telemetry_topic = f"{meter.node.alias}/gt.sh.telemetry.from.multipurpose.sensor.100"
            thermo_telemetry_topic = f"{thermo.node.alias}/gt.telemetry.110"

            # Verify scada status and snapshot are emtpy
            status = scada.make_status()
            snapshot = scada.make_snapshot()
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0
            assert len(snapshot.Snapshot.TelemetryNameList) == 0
            assert len(snapshot.Snapshot.AboutNodeAliasList) == 0
            assert len(snapshot.Snapshot.ValueList) == 0
            assert scada.num_received_by_topic[relay_telemetry_topic] == 0
            assert scada.num_received_by_topic[relay_command_received_topic] == 0
            assert scada.num_received_by_topic[meter_telemetry_topic] == 0
            assert scada.num_received_by_topic[thermo_telemetry_topic] == 0

            # Start sub-actor mqtt but not their sampling threads so that we can ensure they
            # don't send extra reports.
            sub_actors = [relay, meter, thermo]
            for actor in sub_actors:
                actor.start_mqtt()
            self.runner.request_actors(sub_actors)

            # Make sub-actors send their reports
            scada.turn_on(relay.node)
            meter.update_latest_value_dicts()
            meter.report_sampled_telemetry_values(meter.all_power_meter_telemetry_tuples())
            thermo.update_telemetry_value()
            thermo.report_telemetry()

            wait_for(
                lambda: (
                    scada.num_received_by_topic[relay_telemetry_topic] == 1
                    and scada.num_received_by_topic[relay_command_received_topic] == 1
                    and scada.num_received_by_topic[meter_telemetry_topic] == 1
                    and scada.num_received_by_topic[thermo_telemetry_topic] == 1
                ),
                5,
                "Scada wait for reports"
            )

            status = scada.make_status()
            assert len(status.SimpleTelemetryList) == 2
            assert status.SimpleTelemetryList[0].ValueList == [1]
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            assert status.SimpleTelemetryList[1].ShNodeAlias == thermo.node.alias
            assert status.SimpleTelemetryList[1].TelemetryName == TelemetryName.WATER_TEMP_F_TIMES1000
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias
            assert len(status.MultipurposeTelemetryList) == len(scada.my_telemetry_tuples())
            for entry in status.MultipurposeTelemetryList:
                assert entry.SensorNodeAlias == meter.node.alias

            # Cause scada to send a status (and snapshot) now
            scada.last_5_cron_s -= 299

            # Verify Atn got status and snapshot
            wait_for(
                lambda: atn.num_received_by_topic[scada.status_topic] == 1,
                5,
                "Atn wait for status message"
            )
            wait_for(
                lambda: atn.num_received_by_topic[scada.snapshot_topic] == 1,
                5,
                "Atn wait for snapshot message"
            )

            # Verify contents of status and snapshot are as expected
            status = atn.latest_status_payload
            assert isinstance(status, GtShStatus)
            assert len(status.SimpleTelemetryList) == 2
            assert status.SimpleTelemetryList[0].ValueList == [1]
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            assert status.SimpleTelemetryList[1].ShNodeAlias == thermo.node.alias
            assert status.SimpleTelemetryList[1].TelemetryName == TelemetryName.WATER_TEMP_F_TIMES1000
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias
            assert len(status.MultipurposeTelemetryList) == len(scada.my_telemetry_tuples())
            for entry in status.MultipurposeTelemetryList:
                assert entry.SensorNodeAlias == meter.node.alias
            snapshot = atn.latest_snapshot_payload
            assert isinstance(snapshot, SnapshotSpaceheat)
            assert set(snapshot.Snapshot.AboutNodeAliasList) == set(
                [relay.node.alias, thermo.node.alias] + [
                    node.alias for node in meter.all_metered_nodes()
                ]
            )
            assert len(snapshot.Snapshot.AboutNodeAliasList) == 2 + len(meter.all_power_meter_telemetry_tuples())
            assert len(snapshot.Snapshot.ValueList) == len(snapshot.Snapshot.AboutNodeAliasList)

            # Verify scada has cleared its state
            status = scada.make_status()
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0

    FragmentRunner.run_fragment(Fragment)


def test_scada_relay_dispatch():
    """Verify Scada forwards relay dispatch from Atn to relay and that resulting state changes in the relay are
    included in next status and shapshot"""
    class Fragment(ProtocolFragment):

        def __init__(self, runner_: FragmentRunner):
            runner_.actors.scada._scada_atn_fast_dispatch_contract_is_alive_stub = True
            runner_.actors.scada.last_5_cron_s = int(time.time())
            super().__init__(runner_)

        def get_requested_actors(self) -> typing.Sequence[ActorBase]:
            return [self.runner.actors.scada, self.runner.actors.atn]

        def run(self):
            atn = self.runner.actors.atn
            relay = self.runner.actors.relay
            scada = self.runner.actors.scada

            # Verify scada status and snapshot are emtpy
            status = scada.make_status()
            snapshot = scada.make_snapshot()
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0
            assert len(snapshot.Snapshot.TelemetryNameList) == 0
            assert len(snapshot.Snapshot.AboutNodeAliasList) == 0
            assert len(snapshot.Snapshot.ValueList) == 0
            relay_state_topic = f"{relay.node.alias}/gt.telemetry.110"
            relay_command_received_topic = f"{relay.node.alias}/gt.driver.booleanactuator.cmd.100"
            assert scada.num_received_by_topic[relay_state_topic] == 0
            assert scada.num_received_by_topic[relay_command_received_topic] == 0

            # Start the relay and verify it reports its initial state
            relay.start()
            self.runner.request_actors([relay])
            wait_for(
                lambda: scada.num_received_by_topic[relay_state_topic] == 1,
                5,
                "Scada wait for relay state change"
            )
            status = scada.make_status()
            assert len(status.SimpleTelemetryList) == 1
            assert status.SimpleTelemetryList[0].ValueList == [0]
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE

            # Turn on the relay.
            atn.turn_on(relay.node)

            # Verify scada gets telemetry state and command ack.
            wait_for(
                lambda: scada.num_received_by_topic[relay_state_topic] == 1,
                5,
                "Scada wait for relay state change"
            )
            wait_for(
                lambda: scada.num_received_by_topic[relay_command_received_topic] == 1,
                5,
                "Scada wait for relay command received"
            )
            status = scada.make_status()
            assert len(status.SimpleTelemetryList) == 1
            assert status.SimpleTelemetryList[0].ValueList == [0, 1]
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias

            # Cause scada to send a status (and snapshot) now
            scada.last_5_cron_s -= 299

            # Verify Atn got status and snapshot
            wait_for(
                lambda: atn.num_received_by_topic[scada.status_topic] == 1,
                5,
                "Atn wait for status message"
            )
            wait_for(
                lambda: atn.num_received_by_topic[scada.snapshot_topic] == 1,
                5,
                "Atn wait for snapshot message"
            )

            # Verify contents of status and snapshot are as expected
            status = atn.latest_status_payload
            assert isinstance(status, GtShStatus)
            assert len(status.SimpleTelemetryList) == 1
            assert status.SimpleTelemetryList[0].ValueList == [0, 1]
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias
            snapshot = atn.latest_snapshot_payload
            assert isinstance(snapshot, SnapshotSpaceheat)
            assert snapshot.Snapshot.AboutNodeAliasList == [relay.node.alias]
            assert snapshot.Snapshot.ValueList == [1]

            # Verify scada has cleared its state
            status = scada.make_status()
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0

    FragmentRunner.run_fragment(Fragment)
