"""Test Scada"""
import logging
import time
from typing import cast

from gwproto.messages import GtShStatusEvent
from gwproto.messages import SnapshotSpaceheatEvent

from gwproto.data_classes.hardware_layout import HardwareLayout
from tests.atn import AtnSettings
from tests.utils.fragment_runner import Actors
from tests.utils.fragment_runner import AsyncFragmentRunner
from tests.utils.fragment_runner import ProtocolFragment
from tests.utils import ScadaRecorder
from gwproactor_test import await_for
from gwproactor_test.certs import uses_tls
from gwproactor_test.certs import copy_keys

import pytest
from actors import Scada
from actors.config import ScadaSettings
from gwproto.data_classes.telemetry_tuple import TelemetryTuple
from gwproto.enums import TelemetryName
from gwproto.messages import GtShMultipurposeTelemetryStatus
from gwproto.messages import GtShStatus
from gwproto.messages import SnapshotSpaceheat
from data_classes.house_0 import H0N

def test_scada_small():
    settings = ScadaSettings()
    if uses_tls(settings):
        copy_keys("scada", settings)
    settings.paths.mkdirs()
    layout = HardwareLayout.load(settings.paths.hardware_layout)
    scada = Scada(H0N.scada, settings=settings, hardware_layout=layout)
    assert layout.power_meter_node == layout.node(H0N.primary_power_meter)
    meter_node = layout.node(H0N.primary_power_meter)

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


    tt = TelemetryTuple(
        AboutNode=layout.node("store-pump"),
        SensorNode=layout.node(H0N.primary_power_meter),
        TelemetryName=TelemetryName.PowerW,
    )
    scada._data.recent_values_from_multipurpose_sensor[tt] = [43]
    scada._data.recent_read_times_unix_ms_from_multipurpose_sensor[tt] = [
        int(time.time() * 1000)
    ]
    
    s = scada._data.make_multipurpose_telemetry_status(
        tt=cast(TelemetryTuple, "garbage")
    )
    assert s is None

    s = scada._data.make_multipurpose_telemetry_status(tt=tt)
    assert isinstance(s, GtShMultipurposeTelemetryStatus)


    scada.send_status()

    # ##################################
    # # Testing actuation
    # ##################################

    # # test that turn_on and turn_off only work for boolean actuator nodes

    # result = scada.turn_on(meter_node)
    # assert result == ScadaCmdDiagnostic.DISPATCH_NODE_NOT_RELAY
    # result = scada.turn_off(meter_node)
    # assert result == ScadaCmdDiagnostic.DISPATCH_NODE_NOT_RELAY

    #################################
    # Other SCADA small tests
    ##################################

    scada._last_status_second = int(time.time() - 400)
    assert scada.time_to_send_status() is True


# @pytest.mark.asyncio
# async def test_scada_relay_dispatch(tmp_path, monkeypatch, request):
#     """Verify Scada forwards relay dispatch from Atn to relay and that resulting state changes in the relay are
#     included in next status and shapshot"""

#     monkeypatch.chdir(tmp_path)
#     logging.basicConfig(level="DEBUG")
#     settings = ScadaSettings(seconds_per_report=2)
#     if uses_tls(settings):
#         copy_keys("scada", settings)
#     settings.paths.mkdirs(parents=True)
#     atn_settings = AtnSettings()
#     if uses_tls(atn_settings):
#         copy_keys("atn", atn_settings)
#     atn_settings.paths.mkdirs(parents=True)
#     layout = HardwareLayout.load(settings.paths.hardware_layout)
#     actors = Actors(
#         settings,
#         layout=layout,
#         scada=ScadaRecorder(H0N.scada, settings, hardware_layout=layout)
#     )
#     actors.scada._scada_atn_fast_dispatch_contract_is_alive_stub = True
#     actors.scada._last_status_second = int(time.time())
#     actors.scada.suppress_status = True
#     runner = AsyncFragmentRunner(settings, actors=actors, atn_settings=atn_settings, tag=request.node.name)

#     class Fragment(ProtocolFragment):
#         def get_requested_proactors(self):
#             return [self.runner.actors.scada, self.runner.actors.atn]

#         def get_requested_actors(self):
#             return []

#         async def async_run(self):
#             atn = self.runner.actors.atn
#             relay = self.runner.actors.relay
#             scada = self.runner.actors.scada
#             link_stats = scada.stats.links["gridworks"]
#             relay_alias = relay.name
#             relay_node = relay.node

#             # Verify scada status and snapshot are emtpy
#             # TODO: Test public interface
#             status = scada._data.make_status(int(time.time()))
#             snapshot = scada._data.make_snapshot()
#             assert len(status.SimpleTelemetryList) == 0
#             assert len(status.BooleanactuatorCmdList) == 0
#             assert len(status.MultipurposeTelemetryList) == 0
#             assert len(snapshot.Snapshot.TelemetryNameList) == 0
#             assert len(snapshot.Snapshot.AboutNodeAliasList) == 0
#             assert len(snapshot.Snapshot.ValueList) == 0

#             relay_state_message_type = "gt.telemetry"
#             relay_state_topic = f"{relay.name}/{relay_state_message_type}"
#             relay_command_received_topic = f"{relay.name}/gt.driver.booleanactuator.cmd"
#             assert link_stats.num_received_by_topic[relay_state_topic] == 0
#             assert link_stats.num_received_by_topic[relay_command_received_topic] == 0

#             # Wait for relay to report its initial state
#             await await_for(
#                 lambda: scada.stats.num_received_by_type["gt.telemetry"] == 1,
#                 5,
#                 "Scada wait for relay state change",
#                 err_str_f=scada.summary_str
#             )
#             status = scada._data.make_status(int(time.time()))
#             assert len(status.SimpleTelemetryList) == 1
#             assert status.SimpleTelemetryList[0].ValueList == [0]
#             assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
#             assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RelayState

#             # Verify relay is off
#             assert atn.data.latest_snapshot is None
#             atn.snap()
#             await await_for(
#                 lambda: atn.data.latest_snapshot is not None,
#                 3,
#                 "atn did not receive first status",
#             )
#             snapshot1: SnapshotSpaceheat = cast(
#                 SnapshotSpaceheat, atn.data.latest_snapshot
#             )
#             assert isinstance(snapshot1, SnapshotSpaceheat)
#             if snapshot1.Snapshot.AboutNodeAliasList:
#                 relay_idx = snapshot1.Snapshot.AboutNodeAliasList.index(relay_alias)
#                 relay_value = snapshot1.Snapshot.ValueList[relay_idx]
#                 assert relay_value is None or relay_value == 0
#             assert (
#                 relay_node not in scada._data.latest_simple_value
#                 or scada._data.latest_simple_value[relay_node] != 1
#             )

#             # Turn on relay
#             atn.turn_on(relay_node)
#             await await_for(
#                 lambda: scada._data.latest_simple_value[relay_node] == 1,
#                 3,
#                 "scada did not receive update from relay",
#             )
#             status = scada._data.make_status(int(time.time()))
#             assert len(status.SimpleTelemetryList) == 1
#             assert status.SimpleTelemetryList[0].ValueList[-1] == 1
#             assert status.SimpleTelemetryList[0].ShNodeAlias == relay.name
#             assert (
#                 status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RelayState
#             )
#             assert len(status.BooleanactuatorCmdList) == 1
#             assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
#             assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.name

#             # Verify Atn gets updated info for relay
#             atn.snap()
#             await await_for(
#                 lambda: atn.data.latest_snapshot is not None
#                 and id(atn.data.latest_snapshot) != id(snapshot1),
#                 3,
#                 "atn did not receive status",
#             )
#             snapshot2 = atn.data.latest_snapshot
#             assert isinstance(snapshot2, SnapshotSpaceheat)
#             assert (
#                 relay_alias in snapshot2.Snapshot.AboutNodeAliasList
#             ), f"ERROR relay [{relay_alias}] not in {snapshot2.Snapshot.AboutNodeAliasList}"
#             relay_idx = snapshot2.Snapshot.AboutNodeAliasList.index(relay_alias)
#             relay_value = snapshot2.Snapshot.ValueList[relay_idx]
#             assert relay_value == 1

#             # Cause scada to send a status (and snapshot) now
#             snapshots_received = atn.stats.num_received_by_type[SnapshotSpaceheatEvent.model_fields["TypeName"].default]
#             scada.suppress_status = False
#             # Verify Atn got status and snapshot
#             await await_for(
#                 lambda: atn.stats.num_received_by_type[GtShStatusEvent.model_fields["TypeName"].default] == 1,
#                 5,
#                 "Atn wait for status message",
#                 err_str_f=atn.summary_str
#             )
#             await await_for(
#                 lambda: atn.stats.num_received_by_type[SnapshotSpaceheatEvent.model_fields[
#                     "TypeName"].default] == snapshots_received + 1,
#                 5,
#                 "Atn wait for snapshot message",
#                 err_str_f=atn.summary_str,
#             )

#             # Verify contents of status and snapshot are as expected
#             status = atn.data.latest_status
#             assert isinstance(status, GtShStatus)
#             assert len(status.SimpleTelemetryList) == 1
#             assert status.SimpleTelemetryList[0].ValueList[-1] == 1
#             assert status.SimpleTelemetryList[0].ShNodeAlias == relay.name
#             assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RelayState
#             assert len(status.BooleanactuatorCmdList) == 1
#             assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
#             assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.name
#             snapshot = atn.data.latest_snapshot
#             assert isinstance(snapshot, SnapshotSpaceheat)
#             assert snapshot.Snapshot.AboutNodeAliasList == [relay.name]
#             assert snapshot.Snapshot.ValueList == [1]

#             # Verify scada has cleared its state
#             status = scada._data.make_status(int(time.time()))
#             assert len(status.SimpleTelemetryList) == 0
#             assert len(status.BooleanactuatorCmdList) == 0
#             assert len(status.MultipurposeTelemetryList) == 0

#     runner.add_fragment(Fragment(runner))
#     await runner.async_run()


@pytest.mark.asyncio
async def test_scada_periodic_status_delivery(tmp_path, monkeypatch, request):
    """Verify scada periodic status and snapshot"""

    monkeypatch.chdir(tmp_path)
    settings = ScadaSettings(seconds_per_report=2)
    if uses_tls(settings):
        copy_keys("scada", settings)
    settings.paths.mkdirs()
    atn_settings = AtnSettings()
    if uses_tls(atn_settings):
        copy_keys("atn", atn_settings)
    atn_settings.paths.mkdirs()
    layout = HardwareLayout.load(settings.paths.hardware_layout)
    actors = Actors(
        settings,
        layout=layout,
        scada=ScadaRecorder(H0N.scada, settings, hardware_layout=layout),
        atn_settings=atn_settings,
    )
    actors.scada._last_status_second = int(time.time())
    actors.scada.suppress_status = True

    class Fragment(ProtocolFragment):

        def get_requested_proactors(self):
            return [self.runner.actors.scada, self.runner.actors.atn]

        async def async_run(self):
            scada = self.runner.actors.scada
            atn = self.runner.actors.atn
            assert atn.stats.num_received_by_type[GtShStatusEvent.model_fields["TypeName"].default] == 0
            assert atn.stats.num_received_by_type[SnapshotSpaceheatEvent.model_fields["TypeName"].default] == 0
            scada.suppress_status = False
            await await_for(
                lambda: atn.stats.num_received_by_type[GtShStatusEvent.model_fields["TypeName"].default] == 1,
                5,
                "Atn wait for status message"
            )
            await await_for(
                lambda: atn.stats.num_received_by_type[SnapshotSpaceheatEvent.model_fields["TypeName"].default] == 1,
                5,
                "Atn wait for snapshot message"
            )

    runner = AsyncFragmentRunner(settings, actors=actors, atn_settings=atn_settings, tag=request.node.name)
    runner.add_fragment(Fragment(runner))
    await runner.async_run()


@pytest.mark.asyncio
async def test_scada_snaphot_request_delivery(tmp_path, monkeypatch, request):
    """Verify scada sends snapshot upon request from Atn"""

    monkeypatch.chdir(tmp_path)
    settings = ScadaSettings(seconds_per_report=2)

    class Fragment(ProtocolFragment):

        def get_requested_proactors(self):
            self.runner.actors.scada.suppress_status = True
            return [self.runner.actors.scada, self.runner.actors.atn]

        async def async_run(self):
            atn = self.runner.actors.atn
            atn._logger.setLevel(logging.DEBUG)
            assert atn.stats.num_received_by_type[SnapshotSpaceheat.model_fields['TypeName'].default] == 0
            atn._logger.info(SnapshotSpaceheat.model_fields['TypeName'].default)
            atn._logger.info(atn.summary_str())
            atn.snap()
            await await_for(
                lambda: atn.stats.num_received_by_type[SnapshotSpaceheat.model_fields['TypeName'].default] == 1,
                3,
                "Atn wait for snapshot message [test_scada_snaphot_request_delivery]",
                err_str_f=atn.summary_str,
                logger=atn._logger,
            )

    await AsyncFragmentRunner.async_run_fragment(Fragment, settings=settings, tag=request.node.name)


@pytest.mark.asyncio
async def test_scada_status_content_dynamics(tmp_path, monkeypatch, request):
    """Verify Scada status contains command acks from BooleanActuators and telemetry from 
    MultipurposeSensor."""

    monkeypatch.chdir(tmp_path)
    settings = ScadaSettings(seconds_per_report=2)
    if uses_tls(settings):
        copy_keys("scada", settings)
    settings.paths.mkdirs(parents=True)
    atn_settings = AtnSettings()
    layout = HardwareLayout.load(settings.paths.hardware_layout)
    actors = Actors(
        settings,
        layout=layout,
        scada=ScadaRecorder(H0N.scada, settings, hardware_layout=layout),
        atn_settings=atn_settings,
    )
    actors.scada._last_status_second = int(time.time())
    actors.scada.suppress_status = True

    class Fragment(ProtocolFragment):

        def get_requested_proactors(self):
            return [self.runner.actors.scada, self.runner.actors.atn]

        async def async_run(self):
            atn = self.runner.actors.atn
            scada = self.runner.actors.scada
            link_stats = scada.stats.links["gridworks"]
            meter = self.runner.actors.meter
            # telemetry_message_type = "gt.telemetry"
            meter_telemetry_message_type = "gt.sh.telemetry.from.multipurpose.sensor"

            # Verify scada status and snapshot are emtpy
            status = scada._data.make_status(int(time.time()))
            snapshot = scada._data.make_snapshot()
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0
            assert len(snapshot.Snapshot.TelemetryNameList) == 0
            assert len(snapshot.Snapshot.AboutNodeAliasList) == 0
            assert len(snapshot.Snapshot.ValueList) == 0
            #assert link_stats.num_received_by_type[telemetry_message_type] == 0
            assert link_stats.num_received_by_type[meter_telemetry_message_type] == 0

            # Make sub-actors send their reports
            for actor in [meter]:
                scada.add_communicator(actor)
                actor.start()
            await await_for(
                scada._links.link(scada.GRIDWORKS_MQTT).active,
                10,
                "ERROR waiting link active",
                err_str_f=scada.summary_str
            )
            assert scada.scada_atn_fast_dispatch_contract_is_alive
            
            # Provoke a message by increasing the power of elt1
            elt1 = scada._data.hardware_layout.node('elt1')
            tt = TelemetryTuple(
                AboutNode=elt1,
                SensorNode=meter.node,
                TelemetryName=TelemetryName.PowerW,
            )
            meter._sync_thread.latest_telemetry_value[tt] += 300

            await await_for(
                lambda: (
                    #scada.stats.num_received_by_type[telemetry_message_type] >= 3
                    scada.stats.num_received_by_type[meter_telemetry_message_type] >= 1
                ),
                5,
                "Scada wait for reports",
                err_str_f=scada.summary_str
            )

            status = scada._data.make_status(int(time.time()))
            # assert len(status.SimpleTelemetryList) == 2
            # assert status.SimpleTelemetryList[0].ValueList[-1] == 1
            # assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            # assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RelayState
            # assert status.SimpleTelemetryList[1].ShNodeAlias == thermo.node.alias
            # assert status.SimpleTelemetryList[1].TelemetryName == TelemetryName.WaterTempFTimes1000
            # assert len(status.BooleanactuatorCmdList) == 1
            # assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            # assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias
            assert len(status.MultipurposeTelemetryList) == len(self.runner.layout.my_telemetry_tuples)
            for entry in status.MultipurposeTelemetryList:
                assert entry.SensorNodeAlias == meter.node.alias

            # Cause scada to send a status (and snapshot) now
            scada.suppress_status = False

            # Verify Atn got status and snapshot
            await await_for(
                lambda: atn.stats.num_received_by_type[GtShStatusEvent.model_fields["TypeName"].default] == 1,
                5,
                "Atn wait for status message",
                err_str_f=atn.summary_str
            )
            await await_for(
                lambda: atn.stats.num_received_by_type[SnapshotSpaceheatEvent.model_fields["TypeName"].default] == 1,
                5,
                "Atn wait for snapshot message",
                err_str_f=atn.summary_str
            )

            # Verify contents of status and snapshot are as expected
            status = atn.data.latest_status
            assert isinstance(status, GtShStatus)
            # assert len(status.SimpleTelemetryList) == 2
            # assert status.SimpleTelemetryList[0].ValueList == [0, 1]
            # assert status.SimpleTelemetryList[0].ShNodeAlias == relay.node.alias
            # assert status.SimpleTelemetryList[0].TelemetryName == TelemetryName.RelayState
            # assert status.SimpleTelemetryList[1].ShNodeAlias == thermo.node.alias
            # assert status.SimpleTelemetryList[1].TelemetryName == TelemetryName.WaterTempFTimes1000
            # assert len(status.BooleanactuatorCmdList) == 1
            # assert status.BooleanactuatorCmdList[0].RelayStateCommandList == [1]
            # assert status.BooleanactuatorCmdList[0].ShNodeAlias == relay.node.alias
            assert len(status.MultipurposeTelemetryList) == len(self.runner.layout.my_telemetry_tuples)
            for entry in status.MultipurposeTelemetryList:
                assert entry.SensorNodeAlias == meter.node.alias
            snapshot = atn.data.latest_snapshot
            # import pprint
            # pprint.pprint(status.asdict())
            # pprint.pprint(snapshot.asdict())
            assert isinstance(snapshot, SnapshotSpaceheat)
            assert set(snapshot.Snapshot.AboutNodeAliasList) == set(
                [
                    node.alias for node in self.runner.layout.all_nodes_in_agg_power_metering
                ]
            )
            assert len(snapshot.Snapshot.AboutNodeAliasList) ==  \
                len(self.runner.layout.all_power_meter_telemetry_tuples)
            assert len(snapshot.Snapshot.ValueList) == len(snapshot.Snapshot.AboutNodeAliasList)

            # Turn off telemtry reporting
            for actor in [meter]:
                actor.stop()
            for actor in [meter]:
                await actor.join()
            # Wait for scada to send at least one more status.
            statuses_received = atn.stats.total_received(GtShStatusEvent.model_fields["TypeName"].default)
            await await_for(
                lambda: atn.stats.total_received(GtShStatusEvent.model_fields["TypeName"].default) > statuses_received,
                5,
                "Atn wait for status message 2",
                err_str_f=atn.summary_str
            )

            # Verify scada has cleared its state
            status = scada._data.make_status(int(time.time()))
            assert len(status.SimpleTelemetryList) == 0
            assert len(status.BooleanactuatorCmdList) == 0
            assert len(status.MultipurposeTelemetryList) == 0

    runner = AsyncFragmentRunner(settings, actors=actors, atn_settings=atn_settings, tag=request.node.name)
    runner.add_fragment(Fragment(runner))
    await runner.async_run()
