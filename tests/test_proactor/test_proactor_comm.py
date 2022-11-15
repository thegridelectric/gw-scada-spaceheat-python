"""Test communication issues"""
import asyncio

import pytest
from gwproto import MQTTTopic

from config import MQTTClient
from config import ScadaSettings
from proactor.link_state import StateName
from tests.utils.comm_test_helper import CommTestHelper
from tests.utils import await_for

from paho.mqtt.client import MQTT_ERR_CONN_LOST


@pytest.mark.skip()
@pytest.mark.asyncio
async def test_no_broker():
    # no_broker = MQTTClient(host="foo")
    no_broker = MQTTClient(host="www.foo.com")
    async with CommTestHelper(
        settings=ScadaSettings(
            gridworks_mqtt=no_broker,
            local_mqtt=no_broker,
        ),
        start_scada=True,
    ):
        for i in range(2):
            print(f"{i}...")
            await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_no_atn():
    async with CommTestHelper(add_scada=True) as h:
        scada = h.scada
        stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        comm_event_counts = stats.comm_event_counts
        link = scada._link_states.link(scada.GRIDWORKS_MQTT)

        # unstarted scada
        assert stats.num_received == 0
        assert link.state == StateName.not_started

        # start scada
        h.start_scada()
        await await_for(
            link.active_for_send,
            1,
            "ERROR waiting link active_for_send",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_peer
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 2
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Tell client we lost comm.
        scada._mqtt_clients._clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

        # Wait for reconnect
        await await_for(
            lambda: stats.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] > 1,
            3,
            "ERROR waiting link to resubscribe after comm loss",
            err_str_f=scada.summary_str
        )
        assert link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_peer
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert len(stats.comm_events) == 5
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister


@pytest.mark.asyncio
async def test_basic_atn_comm_scada_first():
    async with CommTestHelper(add_scada=True, add_atn=True, verbose=True) as h:
        scada = h.scada
        scada_stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        scada_comm_event_counts = scada_stats.comm_event_counts
        scada_link = scada._link_states.link(scada.GRIDWORKS_MQTT)

        # unstarted scada, atn
        assert scada_stats.num_received == 0
        assert scada_link.state == StateName.not_started

        # start scada
        h.start_scada()
        await await_for(
            scada_link.active_for_send,
            1,
            "ERROR waiting link active_for_send",
            err_str_f=scada.summary_str
        )
        assert not scada_link.active_for_recv()
        assert not scada_link.active()
        assert scada_link.state == StateName.awaiting_peer
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 0
        assert len(scada_stats.comm_events) == 2
        for comm_event in scada_stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # start atn
        h.start_atn()

        # wait for link to go active
        await await_for(
            scada_link.active,
            10,
            "ERROR waiting link active",
            err_str_f=scada.summary_str
        )
        assert scada_link.active_for_recv()
        assert scada_link.active()
        assert scada_link.state == StateName.active
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 1
        assert len(scada_stats.comm_events) == 3

        # wait for all events to be acked
        await await_for(
            lambda: scada._event_persister.num_pending == 0,
            1,
            "ERROR waiting for events to be acked",
            err_str_f=scada.summary_str
        )

        # Tell client we lost comm.
        scada._mqtt_clients._clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

        # Wait for reconnect
        await await_for(
            lambda: scada_stats.comm_event_counts["gridworks.event.comm.peer_active"] > 1,
            3,
            "ERROR waiting link to resubscribe after comm loss",
            err_str_f=scada.summary_str
        )
        assert scada_link.active_for_send()
        assert scada_link.active_for_recv()
        assert scada_link.active()
        assert scada_link.state == StateName.active
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 2
        assert len(scada_stats.comm_events) == 7

        # wait for all events to be acked
        await await_for(
            lambda: scada._event_persister.num_pending == 0,
            1,
            "ERROR waiting for events to be acked",
            err_str_f=scada.summary_str
        )


@pytest.mark.asyncio
async def test_basic_atn_comm_atn_first():
    async with CommTestHelper(add_scada=True, add_atn=True, verbose=True) as h:
        scada = h.scada
        scada_stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        scada_comm_event_counts = scada_stats.comm_event_counts
        scada_link = scada._link_states.link(scada.GRIDWORKS_MQTT)
        atn = h.atn
        atn_link = atn._link_states.link(atn.SCADA_MQTT)

        # unstarted atn
        assert atn_link.state == StateName.not_started

        # start atn
        h.start_atn()
        await await_for(
            atn_link.active_for_send,
            1,
            "ERROR waiting link active_for_send",
            err_str_f=atn.summary_str
        )

        # unstarted scada
        assert scada_stats.num_received == 0
        assert scada_link.state == StateName.not_started

        # start scada
        h.start_scada()
        await await_for(
            scada_link.active,
            1,
            "ERROR waiting link active",
            err_str_f=atn.summary_str
        )

        assert scada_link.active_for_recv()
        assert scada_link.active()
        assert scada_link.state == StateName.active
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 1
        assert len(scada_stats.comm_events) == 3

        # wait for all events to be acked
        await await_for(
            lambda: scada._event_persister.num_pending == 0,
            1,
            "ERROR waiting for events to be acked",
            err_str_f=scada.summary_str
        )

@pytest.mark.asyncio
async def test_basic_atn_comm_loss():
    async with CommTestHelper(add_scada=True, add_atn=True, verbose=True) as h:
        scada = h.scada
        scada_stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        scada_comm_event_counts = scada_stats.comm_event_counts
        scada_link = scada._link_states.link(scada.GRIDWORKS_MQTT)
        atn = h.atn
        atn_link = atn._link_states.link(atn.SCADA_MQTT)

        # unstarted scada, atn
        assert atn_link.state == StateName.not_started
        assert scada_stats.num_received == 0
        assert scada_link.state == StateName.not_started

        # start scada, atn
        h.start_scada()
        h.start_atn()
        await await_for(
            scada_link.active,
            1,
            "ERROR waiting link active",
            err_str_f=scada.summary_str
        )
        assert scada_link.active_for_recv()
        assert scada_link.active()
        assert scada_link.state == StateName.active
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 1
        assert len(scada_stats.comm_events) == 3

        # wait for all events to be acked
        await await_for(
            lambda: scada._event_persister.num_pending == 0,
            1,
            "ERROR waiting for events to be acked",
            err_str_f=scada.summary_str
        )

        # Tell *scada* client we lost comm.
        scada._mqtt_clients._clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

        # Wait for reconnect
        await await_for(
            lambda: scada_stats.comm_event_counts["gridworks.event.comm.peer_active"] > 1,
            3,
            "ERROR waiting link to resubscribe after comm loss",
            err_str_f=scada.summary_str
        )
        assert scada_link.active_for_send()
        assert scada_link.active_for_recv()
        assert scada_link.active()
        assert scada_link.state == StateName.active
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 2
        assert len(scada_stats.comm_events) == 7

        # wait for all events to be acked
        await await_for(
            lambda: scada._event_persister.num_pending == 0,
            1,
            "ERROR waiting for events to be acked",
            err_str_f=scada.summary_str
        )

        # Tell *atn* client we lost comm.
        atn._mqtt_clients._clients[atn.SCADA_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
        # wait for scada to get ping from atn when atn reconnects to mqtt
        atn_ping_topic = MQTTTopic.encode(atn.publication_name, "gw", "gridworks-ping")
        num_atn_pings = scada_stats.num_received_by_topic[atn_ping_topic]
        await await_for(
            lambda: scada_stats.num_received_by_topic[atn_ping_topic] == num_atn_pings + 1,
            3,
            f"ERROR waiting for atn ping {atn_ping_topic}",
            err_str_f=scada.summary_str
        )
        # verify no scada comm state change has occurred.
        assert scada_link.active_for_send()
        assert scada_link.active_for_recv()
        assert scada_link.active()
        assert scada_link.state == StateName.active
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 2
        assert len(scada_stats.comm_events) == 7
        assert scada._event_persister.num_pending == 0


        # Tell *both* clients we lost comm.
        atn._mqtt_clients._clients[atn.SCADA_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
        scada._mqtt_clients._clients[scada.GRIDWORKS_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

        # Wait for reconnect
        await await_for(
            lambda: scada_stats.comm_event_counts["gridworks.event.comm.peer_active"] > 2,
            3,
            "ERROR waiting link to resubscribe after comm loss",
            err_str_f=scada.summary_str
        )
        assert scada_link.active_for_send()
        assert scada_link.active_for_recv()
        assert scada_link.active()
        assert scada_link.state == StateName.active
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 3
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 3
        assert scada_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 2
        assert scada_comm_event_counts["gridworks.event.comm.peer_active"] == 3
        assert len(scada_stats.comm_events) == 11

        # wait for all events to be acked
        await await_for(
            lambda: scada._event_persister.num_pending == 0,
            1,
            "ERROR waiting for events to be acked",
            err_str_f=scada.summary_str
        )


@pytest.mark.asyncio
async def test_separated_subacks_awaiting_setup_and_peer():
    async with CommTestHelper(add_scada=True, verbose=True) as h:
        scada = h.scada
        stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        comm_event_counts = stats.comm_event_counts
        link = scada._link_states.link(scada.GRIDWORKS_MQTT)

        # unstarted scada
        assert stats.num_received == 0
        assert link.state == StateName.not_started

        # start scada
        scada.split_client_subacks(scada.GRIDWORKS_MQTT)
        h.start_scada()
        await await_for(
            link.active_for_send,
            1,
            "ERROR waiting link active_for_send",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_peer
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 2
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Tell client we lost comm.
        scada.pause_subacks()
        scada._mqtt_clients._clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

        await await_for(
            lambda: len(scada.pending_subacks) == 3,
            3,
            "ERROR waiting link reconnect",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup_and_peer

        num_subacks = scada.stats.num_received_by_type["mqtt_suback"]
        scada.release_subacks(1)
        exp_subacks = num_subacks + 1
        await await_for(
            lambda: scada.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
            1,
            f"ERROR waiting mqtt_suback {exp_subacks} (1/3)",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup_and_peer

        scada.release_subacks(1)
        exp_subacks += 1
        await await_for(
            lambda: scada.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
            1,
            f"ERROR waiting mqtt_suback {exp_subacks} (2/3)",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup_and_peer

        scada.release_subacks(1)
        exp_subacks += 1
        await await_for(
            lambda: scada.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
            1,
            f"ERROR waiting mqtt_suback {exp_subacks} (3/3)",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_peer
