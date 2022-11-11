"""Test communication issues"""
from tests.utils.fragment_runner import AsyncFragmentRunner
from tests.utils.fragment_runner import ProtocolFragment
from tests.utils import await_for

import pytest
from paho.mqtt.client import MQTT_ERR_CONN_LOST



@pytest.mark.asyncio
async def test_simple_resubscribe_on_comm_restore2(tmp_path, monkeypatch, request):

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2]

        async def async_run(self):
            return
            # scada = self.runner.actors.scada2
            #
            # await await_for(
            #     lambda: scada.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] > 0,
            #     1,
            #     "ERROR waiting for gw_client subscribe 1",
            #     err_str_f=scada.summary_str
            # )
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            #
            # # Tell client we lost comm.
            # scada._mqtt_clients._clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            #
            # # Wait for disconnect
            # await await_for(
            #     lambda: scada.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] > 0,
            #     1,
            #     "ERROR waiting for gw_client disconnect",
            #     err_str_f=scada.summary_str
            # )
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
            #
            # # Wait for re-subscribe
            # await await_for(
            #     lambda: scada.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] > 1,
            #     5,
            #     "ERROR waiting for gw_client subscribe 2",
            #     err_str_f=scada.summary_str
            # )
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.connect"] == 3
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
            # assert scada.comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1

    await AsyncFragmentRunner.async_run_fragment(Fragment, tag=request.node.name)
