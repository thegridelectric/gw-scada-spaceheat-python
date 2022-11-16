"""Test communication issues"""
import asyncio
import warnings

import pytest
from gwproto import MQTTTopic

from config import MQTTClient
from config import ScadaSettings
from proactor.link_state import StateName
from proactor import proactor_implementation
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
        scada._mqtt_clients._clients[scada.GRIDWORKS_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

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
async def test_awaiting_setup_and_peer():
    """
    Test:
     (connecting -> connected -> awaiting_setup_and_peer)
     (awaiting_setup_and_peer -> mqtt_suback -> awaiting_peer)
     (awaiting_setup_and_peer -> disconnected -> connecting)
    """
    async with CommTestHelper(add_scada=True, verbose=True) as h:
        scada = h.scada
        stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        comm_event_counts = stats.comm_event_counts
        link = scada._link_states.link(scada.GRIDWORKS_MQTT)

        # unstarted scada
        assert stats.num_received == 0
        assert link.state == StateName.not_started

        # start scada
        scada.pause_subacks()
        h.start_scada()
        await await_for(
            lambda: len(scada.pending_subacks) == 1,
            1,
            "ERROR waiting suback pending",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_setup_and_peer
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 1
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Allow suback to arrive
        scada.release_subacks()
        await await_for(
            lambda: link.in_state(StateName.awaiting_peer),
            1,
            f"ERROR waiting mqtt_suback",
            err_str_f=scada.summary_str
        )
        assert link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 2
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Tell client we lost comm
        scada.pause_subacks()
        scada._mqtt_clients._clients[scada.GRIDWORKS_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
        await await_for(
            lambda: len(scada.pending_subacks) == 1,
            3,
            "ERROR waiting suback pending",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_setup_and_peer
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert len(stats.comm_events) == 4
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Tell client we lost comm
        scada.pending_subacks = []
        scada._mqtt_clients._clients[scada.GRIDWORKS_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
        await await_for(
            lambda: len(stats.comm_events) > 4,
            1,
            "ERROR waiting comm fail",
            err_str_f=scada.summary_str
        )
        await await_for(
            lambda: link.in_state(StateName.awaiting_setup_and_peer),
            3,
            "ERROR waiting comm restore",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 3
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 2
        assert len(stats.comm_events) == 6
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Allow suback to arrive
        scada.release_subacks()
        await await_for(
            lambda: link.in_state(StateName.awaiting_peer),
            1,
            f"ERROR waiting mqtt_suback",
            err_str_f=scada.summary_str
        )
        assert link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 3
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 2
        assert len(stats.comm_events) == 7
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

@pytest.mark.asyncio
async def test_awaiting_setup_and_peer_corner_cases():
    """
    Test corner cases:
     (connecting -> connected -> awaiting_setup_and_peer)
     (awaiting_setup_and_peer -> mqtt_suback -> awaiting_setup_and_peer)
     (awaiting_setup_and_peer -> mqtt_suback -> awaiting_peer)
     (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
    Force 1 suback per subscription. By default MQTTClientWrapper packs as many subscriptions as possible into a
    single subscribe message, so by default scada only receives a single suback for all subscriptions.
    So that we can test (awaiting_setup_and_peer -> mqtt_suback -> awaiting_setup_and_peer) self-loop transition,
    which might occur if we have too many subscriptions for that to be possible, we force the suback response to
    be split into multiple messages.

    In practice these might be corner cases that rarely or never occur, since by default all subacks will come and
    one message and we should not receive any messages before subscribing.
    """
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
        scada.pause_subacks()
        h.start_scada()
        await await_for(
            lambda: len(scada.pending_subacks) == 3,
            3,
            "ERROR waiting link reconnect",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup_and_peer
        assert not link.active_for_recv()
        assert not link.active()
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 1
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Allow one suback at a time to arrive
        # suback 1/3
        # (mqtt_suback -> awaiting_setup_and_peer)
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

        # suback 2/3
        # (mqtt_suback -> awaiting_setup_and_peer)
        scada.release_subacks(1)
        exp_subacks += 1
        await await_for(
            lambda: scada.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
            1,
            f"ERROR waiting mqtt_suback {exp_subacks} (2/3)",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup_and_peer

        # suback 3/3
        # (mqtt_suback -> awaiting_peer)
        scada.release_subacks(1)
        exp_subacks += 1
        await await_for(
            lambda: scada.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
            1,
            f"ERROR waiting mqtt_suback {exp_subacks} (3/3)",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_peer
        assert not link.active_for_recv()
        assert not link.active()
        assert link.active_for_send()
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 2
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # (message_from_peer -> awaiting_setup)
        # Tell client we lost comm
        scada.pause_subacks()
        scada._mqtt_clients._clients[scada.GRIDWORKS_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
        await await_for(
            lambda: len(scada.pending_subacks) == 3,
            3,
            "ERROR waiting suback pending",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_setup_and_peer
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert len(stats.comm_events) == 4
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Allow one suback at a time to arrive
        # (Not strictly necessary, since message receiving code does not check if the source topic suback
        #  has arrived).
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

        # Start the atn, wait for it to send us a message, which will
        # transition us into awaiting_setup
        h.add_atn()
        h.start_atn()
        await await_for(
            lambda: link.in_state(StateName.awaiting_setup),
            3,
            "ERROR waiting suback pending",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_setup
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert len(stats.comm_events) == 4

@pytest.mark.asyncio
async def test_awaiting_setup__():
    """
    Test awaiting_setup (corner state):
     (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
     (awaiting_setup -> mqtt_suback -> awaiting_setup)
     (awaiting_setup -> mqtt_suback -> active)
     (awaiting_setup -> message_from_peer -> awaiting_setup)
     (awaiting_setup -> disconnected -> connecting)
    Force 1 suback per subscription. By default MQTTClientWrapper packs as many subscriptions as possible into a
    single subscribe message, so by default scada only receives a single suback for all subscriptions.
    So that we can test (awaiting_setup_and_peer -> mqtt_suback -> awaiting_setup_and_peer) self-loop transition,
    which might occur if we have too many subscriptions for that to be possible, we force the suback response to
    be split into multiple messages.

    In practice these might be corner cases that rarely or never occur, since by default all subacks will come and
    one message and we should not receive any messages before subscribing.
    """
    async with CommTestHelper(add_scada=True, verbose=True) as h:
        scada = h.scada
        stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        comm_event_counts = stats.comm_event_counts
        link = scada._link_states.link(scada.GRIDWORKS_MQTT)

        # unstarted scada
        assert stats.num_received == 0
        assert link.state == StateName.not_started

        # start scada
        # (not_started -> started -> connecting)
        # (connecting -> connected -> awaiting_setup_and_peer)
        scada.split_client_subacks(scada.GRIDWORKS_MQTT)
        scada.pause_subacks()
        h.start_scada()
        await await_for(
            lambda: len(scada.pending_subacks) == 3,
            3,
            "ERROR waiting link reconnect",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup_and_peer
        assert not link.active_for_recv()
        assert not link.active()
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 1
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Allow one suback at a time to arrive
        # (Not strictly necessary, since message receiving code does not check if the source topic suback
        #  has arrived).
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

        # (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
        # Start the atn, wait for it to send us a message, which will
        # transition us into awaiting_setup
        h.add_atn()
        atn = h.start_atn().atn
        await await_for(
            lambda: link.in_state(StateName.awaiting_setup),
            3,
            "ERROR waiting suback pending",
            err_str_f=scada.summary_str
        )
        assert not link.active_for_send()
        assert not link.active_for_recv()
        assert not link.active()
        assert link.state == StateName.awaiting_setup
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
        assert len(stats.comm_events) == 1

        # (awaiting_setup -> mqtt_suback -> awaiting_setup)
        # Allow another suback to arrive, remaining in awaiting_setup
        scada.release_subacks(1)
        exp_subacks = num_subacks + 1
        await await_for(
            lambda: scada.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
            1,
            f"ERROR waiting mqtt_suback {exp_subacks} (1/3)",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup

        # (awaiting_setup -> message_from_peer -> awaiting_setup)
        # Receive another message from peer, remaining in awaiting_setup
        dbg_topic = MQTTTopic.encode(atn.publication_name, "gw", "gridworks.scada.dbg")
        assert stats.num_received_by_topic[dbg_topic] == 0
        atn.dbg()
        await await_for(
            lambda: stats.num_received_by_topic[dbg_topic] == 1,
            1,
            "ERROR waiting for dbg message",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup

        # (awaiting_setup -> disconnected -> connecting)
        # Tell client we lost comm
        scada.pending_subacks.clear()
        scada.pause_subacks()
        scada._mqtt_clients._clients[scada.GRIDWORKS_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
        await await_for(
            lambda: len(scada.pending_subacks) == 3,
            3,
            "ERROR waiting suback pending",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_setup_and_peer
        assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
        assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
        assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
        assert len(stats.comm_events) == 3
        for comm_event in stats.comm_events:
            assert comm_event.MessageId in scada._event_persister

        # Allow one suback at a time to arrive
        # (Not strictly necessary, since message receiving code does not check if the source topic suback
        #  has arrived).
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

        # (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
        # Force atn to restore comm, delivering a message, sending us to awaiting_setup
        atn._mqtt_clients._clients[atn.SCADA_MQTT]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
        await await_for(
            lambda: link.in_state(StateName.awaiting_setup),
            3,
            f"ERROR waiting for message from peer",
            err_str_f=scada.summary_str
        )

        # (awaiting_setup -> mqtt_suback -> active)
        # Release all subacks, allowing scada to go active
        scada.release_subacks()
        await await_for(
            lambda: link.in_state(StateName.active),
            1,
            f"ERROR waiting for active",
            err_str_f=scada.summary_str
        )

@pytest.mark.asyncio
async def test_response_timeout():
    """
    Test:
        (awaiting_peer -> response_timeout -> awaiting_peer)
        (active -> response_timeout -> awaiting_peer)
    """

    async with CommTestHelper(add_scada=True, add_atn=True, verbose=True) as h:
        scada = h.scada
        link = scada._link_states.link(scada.GRIDWORKS_MQTT)
        stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        atn = h.atn
        atn_link = atn._link_states.link(atn.SCADA_MQTT)

        # Timeout while awaiting setup
        # (awaiting_peer -> response_timeout -> awaiting_peer)

        # start atn
        atn.pause_acks()
        h.start_atn()
        await await_for(
            lambda: atn_link.in_state(StateName.awaiting_peer),
            3,
            "ERROR waiting for atn to connect to broker",
            err_str_f=atn.summary_str
        )

        # start scada
        scada.ack_timeout_seconds = .1
        assert stats.timeouts == 0
        h.start_scada()
        await await_for(
            lambda: link.in_state(StateName.awaiting_peer),
            3,
            "ERROR waiting for scada to connect to broker",
            err_str_f=atn.summary_str
        )
        # (awaiting_peer -> response_timeout -> awaiting_peer)
        await await_for(
            lambda: stats.timeouts > 0,
            1,
            "ERROR waiting for scada to timeout",
            err_str_f=atn.summary_str
        )
        assert link.state == StateName.awaiting_peer
        assert scada._event_persister.num_pending > 0

        # release the hounds
        # (awaiting_peer -> message_from_peer -> active)
        atn.release_acks()
        await await_for(
            lambda: link.in_state(StateName.active),
            1,
            "ERROR waiting for atn to restore link #1",
            err_str_f=atn.summary_str
        )
        # wait for all events to be acked
        await await_for(
            lambda: scada._event_persister.num_pending == 0,
                1,
            "ERROR waiting for events to be acked",
            err_str_f=scada.summary_str
        )

        # Timeout while active
        # (active -> response_timeout -> awaiting_peer)
        atn.pause_acks()
        scada.ping_atn()
        exp_timeouts = stats.timeouts + len(scada._acks)
        await await_for(
            lambda: stats.timeouts == exp_timeouts,
            1,
            "ERROR waiting for scada to timeout",
            err_str_f=scada.summary_str
        )
        assert link.state == StateName.awaiting_peer
        assert scada._event_persister.num_pending > 0
        await await_for(
            lambda: len(atn.needs_ack) == 2,
            1,
            "ERROR waiting for scada to timeout",
            err_str_f=scada.summary_str
        )

        # (awaiting_peer -> message_from_peer -> active)
        atn.release_acks()
        await await_for(
            lambda: link.in_state(StateName.active),
            1,
            "ERROR waiting for atn to restore link #1",
            err_str_f=atn.summary_str
        )


@pytest.mark.asyncio
async def test_ping(monkeypatch):
    """
    Test:
        ping sent peridoically if no messages sent
        ping not sent if messages are sent
        ping restores comm
    """
    monkeypatch.setattr(proactor_implementation, "LINK_POLL_SECONDS", .1)
    async with CommTestHelper(add_scada=True, add_atn=True, verbose=False) as h:
        scada = h.scada
        scada.suppress_status = True
        scada.ack_timeout_seconds = .1
        link = scada._link_states.link(scada.GRIDWORKS_MQTT)
        stats = scada.stats.link(scada.GRIDWORKS_MQTT)
        scada_ping_topic = MQTTTopic.encode(scada.publication_name, "gw", "gridworks-ping")
        atn = h.atn
        atn_stats = atn.stats
        atn_ping_topic = MQTTTopic.encode(atn.publication_name, "gw", "gridworks-ping")

        # start atn and scada
        h.start_atn()
        h.start_scada()
        await await_for(
            lambda: link.in_state(StateName.active),
            3,
            "ERROR waiting for scada active",
            err_str_f=scada.summary_str
        )

        # Test that ping sent peridoically if no messages sent
        wait_seconds = .5
        start_pings_from_atn = stats.num_received_by_topic[atn_ping_topic]
        start_pings_from_scada = atn_stats.num_received_by_topic[scada_ping_topic]
        await asyncio.sleep(wait_seconds)
        end_pings_from_atn = stats.num_received_by_topic[atn_ping_topic]
        end_pings_from_scada = atn_stats.num_received_by_topic[scada_ping_topic]
        pings_from_atn = end_pings_from_atn - start_pings_from_atn
        pings_from_scada = end_pings_from_scada - start_pings_from_scada
        exp_pings_nominal = wait_seconds / proactor_implementation.LINK_POLL_SECONDS
        exp_pings = [exp_pings_nominal - 1, exp_pings_nominal, exp_pings_nominal + 1]
        assert pings_from_atn in exp_pings
        assert pings_from_scada in exp_pings

        # Test that ping not sent peridoically if messages are sent
        start_pings_from_atn = stats.num_received_by_topic[atn_ping_topic]
        start_pings_from_scada = atn_stats.num_received_by_topic[scada_ping_topic]
        for _ in range(50):
            atn.dbg()
            await asyncio.sleep(.01)
        end_pings_from_atn = stats.num_received_by_topic[atn_ping_topic]
        end_pings_from_scada = atn_stats.num_received_by_topic[scada_ping_topic]
        pings_from_atn = end_pings_from_atn - start_pings_from_atn
        pings_from_scada = end_pings_from_scada - start_pings_from_scada
        exp_pings = [0, 1, 2]
        if pings_from_atn not in exp_pings:
            warnings.warn(f"Pings not suppressed by other message exchange: pings_from_atn ({pings_from_atn}) not in {exp_pings}")
        if pings_from_scada not in exp_pings:
            warnings.warn(f"Pings not suppressed by other message exchange: pings_from_scada ({pings_from_scada}) not in {exp_pings}")

        atn.pause_acks()
        await await_for(
            lambda: link.in_state(StateName.awaiting_peer),
            1,
            "ERROR waiting for for atn to be slow",
            err_str_f=scada.summary_str
        )
        atn.release_acks(clear=True)
        await await_for(
            lambda: link.in_state(StateName.active),
            1,
            "ERROR waiting for atn to respond",
            err_str_f=scada.summary_str
        )
