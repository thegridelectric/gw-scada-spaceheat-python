"""Test communication issues"""
from tests.fragment_runner import AsyncFragmentRunner
from tests.fragment_runner import ProtocolFragment
from tests.utils import CommEvents
from tests.utils import ScadaRecorder
from tests.utils import await_for
from tests.utils import wait_for

import load_house
import pytest
from config import ScadaSettings
from paho.mqtt.client import MQTT_ERR_CONN_LOST


def test_simple_resubscribe_on_comm_restore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = ScadaSettings()
    settings.paths.mkdirs()
    layout = load_house.load_all(settings)
    scada = ScadaRecorder("a.s", settings=settings, hardware_layout=layout)
    actors = [scada]
    try:
        for actor in actors:
            actor.start()
        # Wait for connect and subscribe
        wait_for(
            lambda: scada.comm_event_counts[CommEvents.subscribe] > 0,
            1,
            "ERROR waiting for gw_client subscribe",
        )
        assert scada.comm_event_counts[CommEvents.connect] == 1
        assert scada.comm_event_counts[CommEvents.subscribe] == 1
        assert scada.comm_event_counts[CommEvents.disconnect] == 0

        # Tell client we lost comm.
        scada.gw_client._loop_rc_handle(MQTT_ERR_CONN_LOST)

        # Wait for disconnect
        wait_for(
            lambda: scada.comm_event_counts[CommEvents.disconnect] > 0,
            1,
            "ERROR waiting for gw_client disconnect",
        )
        assert scada.comm_event_counts[CommEvents.connect] == 1
        assert scada.comm_event_counts[CommEvents.subscribe] == 1
        assert scada.comm_event_counts[CommEvents.disconnect] == 1

        # Wait for re-subscribe
        wait_for(
            lambda: scada.comm_event_counts[CommEvents.subscribe] > 1,
            5,
            "ERROR waiting for gw_client subscribe",
        )
        assert scada.comm_event_counts[CommEvents.connect] == 2
        assert scada.comm_event_counts[CommEvents.subscribe] == 2
        assert scada.comm_event_counts[CommEvents.disconnect] == 1

    finally:
        for actor in actors:
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass


@pytest.mark.asyncio
async def test_simple_resubscribe_on_comm_restore2(tmp_path, monkeypatch):

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2]

        async def async_run(self):
            scada = self.runner.actors.scada2

            await await_for(
                lambda: scada.comm_event_counts[CommEvents.subscribe] > 0,
                1,
                "ERROR waiting for gw_client subscribe 1",
                err_str_f=scada.summary_str
            )
            assert scada.comm_event_counts[CommEvents.connect] == 2
            assert scada.comm_event_counts[CommEvents.subscribe] == 1
            assert scada.comm_event_counts[CommEvents.disconnect] == 0

            # Tell client we lost comm.
            scada._mqtt_clients._clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

            # Wait for disconnect
            await await_for(
                lambda: scada.comm_event_counts[CommEvents.disconnect] > 0,
                1,
                "ERROR waiting for gw_client disconnect",
                err_str_f=scada.summary_str
            )
            assert scada.comm_event_counts[CommEvents.connect] == 2
            assert scada.comm_event_counts[CommEvents.subscribe] == 1
            assert scada.comm_event_counts[CommEvents.disconnect] == 1

            # Wait for re-subscribe
            await await_for(
                lambda: scada.comm_event_counts[CommEvents.subscribe] > 1,
                5,
                "ERROR waiting for gw_client subscribe 2",
                err_str_f=scada.summary_str
            )
            assert scada.comm_event_counts[CommEvents.connect] == 3
            assert scada.comm_event_counts[CommEvents.subscribe] == 2
            assert scada.comm_event_counts[CommEvents.disconnect] == 1

    await AsyncFragmentRunner.async_run_fragment(Fragment)
