"""Test Scada2"""
import logging
import time
import typing

import pytest

import load_house
from actors.scada import ScadaCmdDiagnostic
from actors2 import Scada2
from config import ScadaSettings
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status import (
    GtShBooleanactuatorCmdStatus,
)
from schema.gt.gt_sh_status.gt_sh_status import GtShStatus
from schema.gt.snapshot_spaceheat.snapshot_spaceheat_maker import SnapshotSpaceheat

from schema.gt.gt_sh_multipurpose_telemetry_status.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from schema.gt.gt_sh_simple_telemetry_status.gt_sh_simple_telemetry_status import (
    GtShSimpleTelemetryStatus,
)
from test.fragment_runner import ProtocolFragment, AsyncFragmentRunner, Actors
from test.utils import await_for, Scada2Recorder


def test_scada2_small():
    settings = ScadaSettings()
    layout = load_house.load_all(settings)
    scada = Scada2("a.s", settings=settings, hardware_layout=layout)
    assert layout.power_meter_node == layout.node("a.m")
    meter_node = layout.node("a.m")
    relay_node = layout.node("a.elt1.relay")
    temp_node = layout.node("a.tank.temp0")
    assert list(scada._data.recent_ba_cmds.keys()) == layout.my_boolean_actuators
    assert (
        list(scada._data.recent_ba_cmd_times_unix_ms.keys())
        == layout.my_boolean_actuators
    )
    assert list(scada._data.latest_simple_value.keys()) == layout.my_simple_sensors
    assert list(scada._data.recent_simple_values.keys()) == layout.my_simple_sensors
    assert (
        list(scada._data.recent_simple_read_times_unix_ms.keys())
        == layout.my_simple_sensors
    )
    assert (
        list(scada._data.latest_value_from_multipurpose_sensor.keys())
        == layout.my_telemetry_tuples
    )
    assert (
        list(scada._data.recent_values_from_multipurpose_sensor.keys())
        == layout.my_telemetry_tuples
    )
    assert (
        list(scada._data.recent_read_times_unix_ms_from_multipurpose_sensor.keys())
        == layout.my_telemetry_tuples
    )

    ###########################################
    # Testing making status messages
    ###########################################

    s = scada._data.make_simple_telemetry_status(node=typing.cast(ShNode, "garbage"))
    assert s is None

    scada._data.recent_simple_read_times_unix_ms[temp_node] = [int(time.time() * 1000)]
    scada._data.recent_simple_values[temp_node] = [63000]
    s = scada._data.make_simple_telemetry_status(temp_node)
    assert isinstance(s, GtShSimpleTelemetryStatus)

    tt = TelemetryTuple(
        AboutNode=layout.node("a.elt1"),
        SensorNode=layout.node("a.m"),
        TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
    )
    scada._data.recent_values_from_multipurpose_sensor[tt] = [72000]
    scada._data.recent_read_times_unix_ms_from_multipurpose_sensor[tt] = [
        int(time.time() * 1000)
    ]
    s = scada._data.make_multipurpose_telemetry_status(tt=tt)
    assert isinstance(s, GtShMultipurposeTelemetryStatus)
    s = scada._data.make_multipurpose_telemetry_status(
        tt=typing.cast(TelemetryTuple, "garbage")
    )
    assert s is None

    scada._data.recent_ba_cmds[relay_node] = []
    scada._data.recent_ba_cmd_times_unix_ms[relay_node] = []

    # returns None if asked make boolean actuator status for
    # a node that is not a boolean actuator

    s = scada._data.make_booleanactuator_cmd_status(meter_node)
    assert s is None

    s = scada._data.make_booleanactuator_cmd_status(relay_node)
    assert s is None

    scada._data.recent_ba_cmds[relay_node] = [0]
    scada._data.recent_ba_cmd_times_unix_ms[relay_node] = [int(time.time() * 1000)]
    s = scada._data.make_booleanactuator_cmd_status(relay_node)
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

    scada._last_status_second = int(time.time() - 400)
    assert scada.time_to_send_status() is True


@pytest.mark.asyncio
async def test_scada2_relay_dispatch(tmp_path, monkeypatch):
    """Verify Scada forwards relay dispatch from Atn to relay and that resulting state changes in the relay are
    included in next status and shapshot"""

    monkeypatch.chdir(tmp_path)
    logging.basicConfig(level="DEBUG")
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)
    settings = ScadaSettings(seconds_per_report=2)
    layout = load_house.load_all(settings)
    actors = Actors(
        settings,
        layout=layout,
        scada2=Scada2Recorder("a.s", settings, hardware_layout=layout)
    )
    actors.scada2._scada_atn_fast_dispatch_contract_is_alive_stub = True
    actors.scada2._last_status_second = int(time.time())
    actors.scada2.suppress_status = True
    runner = AsyncFragmentRunner(settings, actors=actors)

    class Fragment(ProtocolFragment):
        def get_requested_actors(self):
            return [self.runner.actors.scada2, self.runner.actors.atn]

        def get_requested_actors2(self):
            return [self.runner.actors.relay2]

        async def async_run(self):
            atn = self.runner.actors.atn
            relay2 = self.runner.actors.relay2
            scada2 = self.runner.actors.scada2
            relay_alias = relay2.alias
            relay_node = relay2.node

            # Verify scada status and snapshot are emtpy
            # TODO: Test public interface
            status = scada2._data.make_status(int(time.time()))
            snapshot = scada2._data.make_snapshot()
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0
            assert len(snapshot.Snapshot.TelemetryNameList) == 0
            assert len(snapshot.Snapshot.AboutNodeAliasList) == 0
            assert len(snapshot.Snapshot.ValueList) == 0

            relay_state_message_type = "gt.telemetry.110"
            relay_state_topic = f"{relay2.alias}/{relay_state_message_type}"
            relay_command_received_topic = f"{relay2.alias}/gt.driver.booleanactuator.cmd.100"
            assert scada2.num_received_by_topic[relay_state_topic] == 0
            assert scada2.num_received_by_topic[relay_command_received_topic] == 0

            # Start the relay and verify it reports its initial state
            await await_for(
                lambda: scada2.num_received_by_type["gt.telemetry.110"] == 1,
                5,
                "Scada wait for relay state change",
            )
            status = scada2._data.make_status(int(time.time()))
            assert len(status.SimpleTelemetryList) == 1
            assert status.SimpleTelemetryList[0].ValueList == [0]
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay2.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE

            # Verify relay is off
            assert atn.latest_snapshot_payload is None
            atn.status()
            await await_for(
                lambda: atn.latest_snapshot_payload is not None,
                3,
                "atn did not receive first status",
            )
            snapshot1: SnapshotSpaceheat = typing.cast(
                SnapshotSpaceheat, atn.latest_snapshot_payload
            )
            assert isinstance(snapshot1, SnapshotSpaceheat)
            if snapshot1.Snapshot.AboutNodeAliasList:
                relay_idx = snapshot1.Snapshot.AboutNodeAliasList.index(relay_alias)
                relay_value = snapshot1.Snapshot.ValueList[relay_idx]
                assert relay_value is None or relay_value == 0
            assert (
                relay_node not in scada2._data.latest_simple_value
                or scada2._data.latest_simple_value[relay_node] != 1
            )

            # Turn on relay
            atn.turn_on(relay_node)
            await await_for(
                lambda: scada2._data.latest_simple_value[relay_node] == 1,
                3,
                "scada did not receive update from relay",
            )
            status = scada2._data.make_status(int(time.time()))
            assert len(status.SimpleTelemetryList) == 1
            assert status.SimpleTelemetryList[0].ValueList[-1] == 1
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay2.alias
            assert (
                status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            )
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay2.alias

            # Verify Atn gets updated info for relay
            atn.status()
            await await_for(
                lambda: atn.latest_snapshot_payload is not None
                and id(atn.latest_snapshot_payload) != id(snapshot1),
                3,
                "atn did not receive status",
            )
            snapshot2 = atn.latest_snapshot_payload
            assert isinstance(snapshot2, SnapshotSpaceheat)
            assert (
                relay_alias in snapshot2.Snapshot.AboutNodeAliasList
            ), f"ERROR relay [{relay_alias}] not in {snapshot2.Snapshot.AboutNodeAliasList}"
            relay_idx = snapshot2.Snapshot.AboutNodeAliasList.index(relay_alias)
            relay_value = snapshot2.Snapshot.ValueList[relay_idx]
            assert relay_value == 1

            # Cause scada to send a status (and snapshot) now
            snapshots_received = atn.num_received_by_topic[scada2.snapshot_topic]
            scada2.suppress_status = False
            # Verify Atn got status and snapshot
            await await_for(
                lambda: atn.num_received_by_topic[scada2.status_topic] == 1,
                5,
                "Atn wait for status message"
            )
            print(atn.num_received_by_topic[scada2.snapshot_topic])
            await await_for(
                lambda: atn.num_received_by_topic[scada2.snapshot_topic] == snapshots_received + 1,
                5,
                "Atn wait for snapshot message",
                err_str_f=atn.summary_str,
            )

            # Verify contents of status and snapshot are as expected
            status = atn.latest_status_payload
            assert isinstance(status, GtShStatus)
            assert len(status.SimpleTelemetryList) == 1
            assert status.SimpleTelemetryList[0].ValueList[-1] == 1
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay2.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay2.alias
            snapshot = atn.latest_snapshot_payload
            assert isinstance(snapshot, SnapshotSpaceheat)
            assert snapshot.Snapshot.AboutNodeAliasList == [relay2.alias]
            assert snapshot.Snapshot.ValueList == [1]

            # Verify scada has cleared its state
            status = scada2._data.make_status(int(time.time()))
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0

    runner.add_fragment(Fragment(runner))
    await runner.async_run()


@pytest.mark.asyncio
async def test_scada2_periodic_status_delivery(tmp_path, monkeypatch):
    """Verify scada periodic status and snapshot"""

    monkeypatch.chdir(tmp_path)
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)
    settings = ScadaSettings(seconds_per_report=2)
    layout = load_house.load_all(settings)
    actors = Actors(
        settings,
        layout=layout,
        scada2=Scada2Recorder("a.s", settings, hardware_layout=layout)
    )
    actors.scada2._last_status_second = int(time.time())
    actors.scada2.suppress_status = True

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2, self.runner.actors.atn]

        async def async_run(self):
            scada2 = self.runner.actors.scada2
            atn = self.runner.actors.atn
            assert atn.num_received_by_topic[scada2.status_topic] == 0
            assert atn.num_received_by_topic[scada2.snapshot_topic] == 0
            scada2.suppress_status = False
            await await_for(
                lambda: atn.num_received_by_topic[scada2.status_topic] == 1,
                5,
                "Atn wait for status message"
            )
            await await_for(
                lambda: atn.num_received_by_topic[scada2.snapshot_topic] == 1,
                5,
                "Atn wait for snapshot message"
            )

    runner = AsyncFragmentRunner(settings, actors=actors)
    runner.add_fragment(Fragment(runner))
    await runner.async_run()


@pytest.mark.asyncio
async def test_scada2_snaphot_request_delivery():
    """Verify scada sends snapshot upon request from Atn"""

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2, self.runner.actors.atn]

        async def async_run(self):
            scada2 = self.runner.actors.scada2
            atn = self.runner.actors.atn
            assert atn.num_received_by_topic[scada2.snapshot_topic] == 0
            atn.status()
            await await_for(
                lambda: atn.num_received_by_topic[scada2.snapshot_topic] == 1,
                10,
                "Atn wait for snapshot message"
            )

    await AsyncFragmentRunner.async_run_fragment(Fragment)


@pytest.mark.asyncio
async def test_scada2_status_content_dynamics(tmp_path, monkeypatch):
    """Verify Scada status contains command acks from BooleanActuators and telemetry from SimpleSensor and
    MultipurposeSensor."""

    monkeypatch.chdir(tmp_path)
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)
    settings = ScadaSettings(seconds_per_report=2)
    layout = load_house.load_all(settings)
    actors = Actors(
        settings,
        layout=layout,
        scada2=Scada2Recorder("a.s", settings, hardware_layout=layout)
    )
    actors.scada2._last_status_second = int(time.time())
    actors.scada2.suppress_status = True

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2, self.runner.actors.atn]

        async def async_run(self):
            atn = self.runner.actors.atn
            scada = self.runner.actors.scada2
            relay = self.runner.actors.relay2
            meter = self.runner.actors.meter2
            thermo = self.runner.actors.thermo2
            telemetry_message_type = "gt.telemetry.110"
            meter_telemetry_message_type = "gt.sh.telemetry.from.multipurpose.sensor.100"

            # Verify scada status and snapshot are emtpy
            status = scada._data.make_status(int(time.time()))
            snapshot = scada._data.make_snapshot()
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0
            assert len(snapshot.Snapshot.TelemetryNameList) == 0
            assert len(snapshot.Snapshot.AboutNodeAliasList) == 0
            assert len(snapshot.Snapshot.ValueList) == 0
            assert scada.num_received_by_type[telemetry_message_type] == 0
            assert scada.num_received_by_type[meter_telemetry_message_type] == 0

            # Make sub-actors send their reports
            for actor in [thermo, relay, meter]:
                scada.add_communicator(actor)
                actor.start()
            scada.turn_on(relay.node)

            await await_for(
                lambda: (
                    scada.num_received_by_type[telemetry_message_type] >= 3
                    and scada.num_received_by_type[meter_telemetry_message_type] >= 1
                ),
                5,
                "Scada wait for reports",
                err_str_f=scada.summary_str
            )

            status = scada._data.make_status(int(time.time()))
            assert len(status.SimpleTelemetryList) == 2
            assert status.SimpleTelemetryList[0].ValueList[-1] == 1
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            assert status.SimpleTelemetryList[1].ShNodeAlias == thermo.node.alias
            assert status.SimpleTelemetryList[1].TelemetryName == TelemetryName.WATER_TEMP_F_TIMES1000
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias
            assert len(status.MultipurposeTelemetryList) == len(self.runner.layout.my_telemetry_tuples)
            for entry in status.MultipurposeTelemetryList:
                assert entry.SensorNodeAlias == meter.node.alias

            # Cause scada to send a status (and snapshot) now
            scada.suppress_status = False

            # Verify Atn got status and snapshot
            await await_for(
                lambda: atn.num_received_by_topic[scada.status_topic] == 1,
                5,
                "Atn wait for status message"
            )
            await await_for(
                lambda: atn.num_received_by_topic[scada.snapshot_topic] == 1,
                5,
                "Atn wait for snapshot message"
            )

            # Verify contents of status and snapshot are as expected
            status = atn.latest_status_payload
            assert isinstance(status, GtShStatus)
            assert len(status.SimpleTelemetryList) == 2
            assert status.SimpleTelemetryList[0].ValueList == [0, 1]
            assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RELAY_STATE
            assert status.SimpleTelemetryList[1].ShNodeAlias == thermo.node.alias
            assert status.SimpleTelemetryList[1].TelemetryName == TelemetryName.WATER_TEMP_F_TIMES1000
            assert len(status.BooleanactuatorCmdList) == 1
            assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias
            assert len(status.MultipurposeTelemetryList) == len(self.runner.layout.my_telemetry_tuples)
            for entry in status.MultipurposeTelemetryList:
                assert entry.SensorNodeAlias == meter.node.alias
            snapshot = atn.latest_snapshot_payload
            # import pprint
            # pprint.pprint(status.asdict())
            # pprint.pprint(snapshot.asdict())
            assert isinstance(snapshot, SnapshotSpaceheat)
            assert set(snapshot.Snapshot.AboutNodeAliasList) == set(
                [relay.node.alias, thermo.node.alias] + [
                    node.alias for node in self.runner.layout.all_metered_nodes
                ]
            )
            assert len(snapshot.Snapshot.AboutNodeAliasList) == 2 + \
                len(self.runner.layout.all_power_meter_telemetry_tuples)
            assert len(snapshot.Snapshot.ValueList) == len(snapshot.Snapshot.AboutNodeAliasList)

            # Turn off telemtry reporting
            for actor in [thermo, relay, meter]:
                actor.stop()
            for actor in [thermo, relay, meter]:
                await actor.join()
            # Wait for scada to send at least one more status.
            statuses_received = atn.num_received_by_topic[scada.status_topic]
            await await_for(
                lambda: atn.num_received_by_topic[scada.status_topic] > statuses_received,
                5,
                "Atn wait for status message 2",
                err_str_f=atn.summary_str
            )

            # Verify scada has cleared its state
            status = scada._data.make_status(int(time.time()))
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0

    runner = AsyncFragmentRunner(settings, actors=actors)
    runner.add_fragment(Fragment(runner))
    await runner.async_run()
