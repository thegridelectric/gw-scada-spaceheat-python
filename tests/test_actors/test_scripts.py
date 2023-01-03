"""Test code very similar to the scripts provided by the repo"""
import asyncio
import os
from tests.conftest import TEST_DOTENV_PATH
from tests.conftest import TEST_DOTENV_PATH_VAR
from tests.utils.fragment_runner import AsyncFragmentRunner
from tests.utils.fragment_runner import ProtocolFragment
from tests.utils import await_for

import load_house
import pytest
from command_line_utils import run_async_actors_main
from command_line_utils import run_nodes_main
from actors2.config import ScadaSettings
from schema.enums import Role
from gwproto.messages import  GtShStatus
from gwproto.messages import  GtShStatus_Maker
from gwproto.messages import  SnapshotSpaceheat
from gwproto.messages import  SnapshotSpaceheat_Maker


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
            argv=["-n", *aliases, "-e", os.getenv(TEST_DOTENV_PATH_VAR, TEST_DOTENV_PATH)],
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


def test_run_local(tmp_path):
    """Test the "run_local" script semantics"""
    layout = load_house.load_all(ScadaSettings())

    aliases = [
        node.alias
        for node in filter(lambda x: (x.role != Role.ATN and x.has_actor), layout.nodes.values())
    ]
    test_run_nodes_main(aliases)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run_local2(tmp_path, monkeypatch, request):

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SCADA_SECONDS_PER_REPORT", "2")
    settings = ScadaSettings()
    assert settings.seconds_per_report == 2
    status_topic = GtShStatus_Maker.type_alias
    snapshot_topic = SnapshotSpaceheat_Maker.type_alias

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.atn]

        async def async_run(self):
            atn = self.runner.actors.atn
            argv = ["-n", "-e", os.getenv(TEST_DOTENV_PATH_VAR, TEST_DOTENV_PATH)]
            for node in self.runner.layout.nodes.values():
                if node.role != Role.ATN and node.role != Role.HOME_ALONE and node.has_actor:
                    argv.append(node.alias)
                    if node.role != Role.SCADA:
                        node.reporting_sample_period_s = 1
            script_task = asyncio.create_task(run_async_actors_main(argv=argv))
            try:
                # Verify Atn got status and snapshot
                await await_for(
                    lambda: atn.num_received_by_topic[status_topic] == 3,
                    10,
                    "Atn wait for status message"
                )
                await await_for(
                    lambda: atn.num_received_by_topic[snapshot_topic] >= 3,
                    10,
                    "Atn wait for snapshot message"
                )

                # Verify contents of status and snapshot are as expected
                # TODO: A more comprehensive tests of results. These checks merely assert the reporting sensors
                #       are as seen in the first experiment
                status = atn.latest_status_payload
                assert isinstance(status, GtShStatus)
                assert len(status.SimpleTelemetryList) == 10
                assert len(status.MultipurposeTelemetryList) == len(self.runner.layout.my_telemetry_tuples)
                snapshot = atn.latest_snapshot_payload
                assert isinstance(snapshot, SnapshotSpaceheat)
                assert len(snapshot.Snapshot.ValueList) == len(
                    status.SimpleTelemetryList) + len(self.runner.layout.my_telemetry_tuples)
                assert len(snapshot.Snapshot.ValueList) == len(snapshot.Snapshot.AboutNodeAliasList)
            finally:
                script_task.cancel()
                try:
                    await script_task
                except asyncio.exceptions.CancelledError:
                    pass
                except Exception as e:
                    print(e)

    await AsyncFragmentRunner.async_run_fragment(Fragment, tag=request.node.name)
