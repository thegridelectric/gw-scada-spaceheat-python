"""Test communication issues"""

from paho.mqtt.client import MQTT_ERR_CONN_LOST

import load_house
from config import ScadaSettings
from test.utils import ScadaRecorder, wait_for, CommEvents


def test_simple_resubscribe_on_comm_restore(tmp_path, monkeypatch):
    """Run various nodes and verify they send each other messages as expected"""
    monkeypatch.chdir(tmp_path)
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)
    settings = ScadaSettings()
    layout=load_house.load_all(settings)
    scada = ScadaRecorder(node=layout.node("a.s"), settings=settings, hardware_layout=layout)
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
