import asyncio
import warnings
from typing import Type

import pytest
from gwproto import MQTTTopic
from paho.mqtt.client import MQTT_ERR_CONN_LOST

from gwproactor.config import MQTTClient
from gwproactor.link_state import StateName
from gwproactor.message import DBGPayload
from tests.utils import await_for
from tests.utils.comm_test_helper import CommTestHelper
from tests.utils.proactor_dummies import DummyChildSettings


@pytest.mark.asyncio
class ProactorCommTests:
    CTH: Type[CommTestHelper]

    async def test_no_parent(self):
        async with self.CTH(add_child=True) as h:
            child = h.child
            stats = child.stats.link(child.upstream_client)
            comm_event_counts = stats.comm_event_counts
            link = child._link_states.link(child.upstream_client)

            # unstarted child
            assert stats.num_received == 0
            assert link.state == StateName.not_started

            # start child
            h.start_child()
            await await_for(
                link.active_for_send,
                1,
                "ERROR waiting link active_for_send",
                err_str_f=child.summary_str
            )
            assert not link.active_for_recv()
            assert not link.active()
            assert link.state == StateName.awaiting_peer
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert len(stats.comm_events) == 2
            for comm_event in stats.comm_events:
                assert comm_event.MessageId in child._event_persister

            # Tell client we lost comm.
            child._mqtt_clients.clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

            # Wait for reconnect
            await await_for(
                lambda: stats.comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] > 1,
                3,
                "ERROR waiting link to resubscribe after comm loss",
                err_str_f=child.summary_str
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
                assert comm_event.MessageId in child._event_persister

    async def test_basic_comm_child_first(self):
        async with self.CTH(add_child=True, add_parent=True, verbose=True, parent_on_screen=True) as h:
            child = h.child
            child_stats = child.stats.link(child.upstream_client)
            child_comm_event_counts = child_stats.comm_event_counts
            child_link = child._link_states.link(child.upstream_client)

            # unstarted child, parent
            assert child_stats.num_received == 0
            assert child_link.state == StateName.not_started

            # start child
            h.start_child()
            await await_for(
                child_link.active_for_send,
                1,
                "ERROR waiting link active_for_send",
                err_str_f=child.summary_str
            )
            assert not child_link.active_for_recv()
            assert not child_link.active()
            assert child_link.state == StateName.awaiting_peer
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 0
            assert len(child_stats.comm_events) == 2
            for comm_event in child_stats.comm_events:
                assert comm_event.MessageId in child._event_persister

            # start parent
            h.start_parent()

            # wait for link to go active
            await await_for(
                child_link.active,
                10,
                "ERROR waiting link active",
                err_str_f=child.summary_str
            )
            assert child_link.active_for_recv()
            assert child_link.active()
            assert child_link.state == StateName.active
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 1
            assert len(child_stats.comm_events) == 3

            # wait for all events to be acked
            await await_for(
                lambda: child._event_persister.num_pending == 0,
                1,
                "ERROR waiting for events to be acked",
                err_str_f=child.summary_str
            )

            # Tell client we lost comm.
            child._mqtt_clients.clients["gridworks"]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

            # Wait for reconnect
            await await_for(
                lambda: child_stats.comm_event_counts["gridworks.event.comm.peer_active"] > 1,
                3,
                "ERROR waiting link to resubscribe after comm loss",
                err_str_f=child.summary_str
            )
            assert child_link.active_for_send()
            assert child_link.active_for_recv()
            assert child_link.active()
            assert child_link.state == StateName.active
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 2
            assert len(child_stats.comm_events) == 7

            # wait for all events to be acked
            await await_for(
                lambda: child._event_persister.num_pending == 0,
                1,
                "ERROR waiting for events to be acked",
                err_str_f=child.summary_str
            )

    @pytest.mark.skip()
    @pytest.mark.asyncio
    async def test_broker_dns_failure(self):
        """Verify proactor does not crash in presence of bad host.

        This test skipped because it's currently very slow - 4 seconds
        before mqtt client thread reports first problem.

        A better test would:
            - be faster
            - verify client thread continues
            - verify problem reports occur
            - possibly verify that eventually child requests device restart since pi's are
              having DNS failures on network comm loss that seem to be undone by pi restart
        """
        no_broker = MQTTClient(host="www.foo.com")
        async with self.CTH(
            child_settings=DummyChildSettings(
                parent_mqtt=no_broker,
            ),
            start_child=True,
            verbose=True,
        ):
            for i in range(20):
                print(f"{i}...")
                await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_basic_comm_parent_first(self):
        async with self.CTH(add_child=True, add_parent=True, verbose=True) as h:
            child = h.child
            child_stats = child.stats.link(child.upstream_client)
            child_comm_event_counts = child_stats.comm_event_counts
            child_link = child._link_states.link(child.upstream_client)
            parent = h.parent
            #TODO: hack
            parent_link = parent._link_states.link(parent.primary_peer_client)

            # unstarted parent
            assert parent_link.state == StateName.not_started

            # start parent
            h.start_parent()
            await await_for(
                parent_link.active_for_send,
                1,
                "ERROR waiting link active_for_send",
                err_str_f=parent.summary_str
            )

            # unstarted child
            assert child_stats.num_received == 0
            assert child_link.state == StateName.not_started

            # start child
            h.start_child()
            await await_for(
                child_link.active,
                1,
                "ERROR waiting link active",
                err_str_f=parent.summary_str
            )

            assert child_link.active_for_recv()
            assert child_link.active()
            assert child_link.state == StateName.active
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 1
            assert len(child_stats.comm_events) == 3

            # wait for all events to be acked
            await await_for(
                lambda: child._event_persister.num_pending == 0,
                1,
                "ERROR waiting for events to be acked",
                err_str_f=child.summary_str
            )

    @pytest.mark.asyncio
    async def test_basic_parent_comm_loss(self):
        async with self.CTH(add_child=True, add_parent=True, verbose=False) as h:
            child = h.child
            child_stats = child.stats.link(child.upstream_client)
            child_comm_event_counts = child_stats.comm_event_counts
            child_link = child._link_states.link(child.upstream_client)
            parent = h.parent
            parent_link = parent._link_states.link(parent.primary_peer_client)

            # unstarted child, parent
            assert parent_link.state == StateName.not_started
            assert child_stats.num_received == 0
            assert child_link.state == StateName.not_started

            # start child, parent
            h.start_child()
            h.start_parent()
            await await_for(
                child_link.active,
                1,
                "ERROR waiting link active",
                err_str_f=child.summary_str
            )
            assert child_link.active_for_recv()
            assert child_link.active()
            assert child_link.state == StateName.active
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 1
            assert len(child_stats.comm_events) == 3

            # wait for all events to be acked
            await await_for(
                lambda: child._event_persister.num_pending == 0,
                1,
                "ERROR waiting for events to be acked",
                err_str_f=child.summary_str
            )

            # Tell *child* client we lost comm.
            child._mqtt_clients.clients[child.upstream_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

            # Wait for reconnect
            await await_for(
                lambda: child_stats.comm_event_counts["gridworks.event.comm.peer_active"] > 1,
                3,
                "ERROR waiting link to resubscribe after comm loss",
                err_str_f=child.summary_str
            )
            assert child_link.active_for_send()
            assert child_link.active_for_recv()
            assert child_link.active()
            assert child_link.state == StateName.active
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 2
            assert len(child_stats.comm_events) == 7

            # wait for all events to be acked
            await await_for(
                lambda: child._event_persister.num_pending == 0,
                1,
                "ERROR waiting for events to be acked",
                err_str_f=child.summary_str
            )

            # Tell *parent* client we lost comm.
            parent._mqtt_clients.clients[parent.primary_peer_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            # wait for child to get ping from parent when parent reconnects to mqtt
            parent_ping_topic = MQTTTopic.encode("gw", parent.publication_name, "gridworks-ping")
            num_parent_pings = child_stats.num_received_by_topic[parent_ping_topic]
            await await_for(
                lambda: child_stats.num_received_by_topic[parent_ping_topic] == num_parent_pings + 1,
                3,
                f"ERROR waiting for parent ping {parent_ping_topic}",
                err_str_f=child.summary_str
            )
            # verify no child comm state change has occurred.
            assert child_link.active_for_send()
            assert child_link.active_for_recv()
            assert child_link.active()
            assert child_link.state == StateName.active
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 2
            assert len(child_stats.comm_events) == 7
            assert child._event_persister.num_pending == 0

            # Tell *both* clients we lost comm.
            parent._mqtt_clients.clients[parent.primary_peer_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            child._mqtt_clients.clients[child.upstream_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)

            # Wait for reconnect
            await await_for(
                lambda: child_stats.comm_event_counts["gridworks.event.comm.peer_active"] > 2,
                3,
                "ERROR waiting link to resubscribe after comm loss",
                err_str_f=child.summary_str
            )
            assert child_link.active_for_send()
            assert child_link.active_for_recv()
            assert child_link.active()
            assert child_link.state == StateName.active
            assert child_comm_event_counts["gridworks.event.comm.mqtt.connect"] == 3
            assert child_comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 3
            assert child_comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 2
            assert child_comm_event_counts["gridworks.event.comm.peer_active"] == 3
            assert len(child_stats.comm_events) == 11

            # wait for all events to be acked
            await await_for(
                lambda: child._event_persister.num_pending == 0,
                1,
                "ERROR waiting for events to be acked",
                err_str_f=child.summary_str
            )

    @pytest.mark.asyncio
    async def test_awaiting_setup_and_peer2(self):
        """
        Test:
         (connecting -> connected -> awaiting_setup_and_peer)
         (awaiting_setup_and_peer -> mqtt_suback -> awaiting_peer)
         (awaiting_setup_and_peer -> disconnected -> connecting)
        """
        async with self.CTH(add_child=True, verbose=True) as h:
            child = h.child
            stats = child.stats.link(child.upstream_client)
            comm_event_counts = stats.comm_event_counts
            link = child._link_states.link(child.upstream_client)

            # unstarted child
            assert stats.num_received == 0
            assert link.state == StateName.not_started

            # start child
            child.pause_subacks()
            h.start_child()
            await await_for(
                lambda: len(child.pending_subacks) == 1,
                1,
                "ERROR waiting suback pending",
                err_str_f=child.summary_str
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
                assert comm_event.MessageId in child._event_persister

            # Allow suback to arrive
            child.release_subacks()
            await await_for(
                lambda: link.in_state(StateName.awaiting_peer),
                1,
                f"ERROR waiting mqtt_suback",
                err_str_f=child.summary_str
            )
            assert link.active_for_send()
            assert not link.active_for_recv()
            assert not link.active()
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert len(stats.comm_events) == 2
            for comm_event in stats.comm_events:
                assert comm_event.MessageId in child._event_persister

            # Tell client we lost comm
            child.pause_subacks()
            child._mqtt_clients.clients[child.upstream_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            await await_for(
                lambda: len(child.pending_subacks) == 1,
                3,
                "ERROR waiting suback pending",
                err_str_f=child.summary_str
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
                assert comm_event.MessageId in child._event_persister

            # Tell client we lost comm
            child.pending_subacks = []
            child._mqtt_clients.clients[child.upstream_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            await await_for(
                lambda: len(stats.comm_events) > 4,
                1,
                "ERROR waiting comm fail",
                err_str_f=child.summary_str
            )
            await await_for(
                lambda: link.in_state(StateName.awaiting_setup_and_peer),
                3,
                "ERROR waiting comm restore",
                err_str_f=child.summary_str
            )
            assert not link.active_for_send()
            assert not link.active_for_recv()
            assert not link.active()
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 3
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 2
            assert len(stats.comm_events) == 6
            for comm_event in stats.comm_events:
                assert comm_event.MessageId in child._event_persister

            # Allow suback to arrive
            child.release_subacks()
            await await_for(
                lambda: link.in_state(StateName.awaiting_peer),
                1,
                f"ERROR waiting mqtt_suback",
                err_str_f=child.summary_str
            )
            assert link.active_for_send()
            assert not link.active_for_recv()
            assert not link.active()
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 3
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 2
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 2
            assert len(stats.comm_events) == 7
            for comm_event in stats.comm_events:
                assert comm_event.MessageId in child._event_persister

    @pytest.mark.asyncio
    async def test_awaiting_setup_and_peer_corner_cases2(self):
        """
        Test corner cases:
         (connecting -> connected -> awaiting_setup_and_peer)
         (awaiting_setup_and_peer -> mqtt_suback -> awaiting_setup_and_peer)
         (awaiting_setup_and_peer -> mqtt_suback -> awaiting_peer)
         (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
        Force 1 suback per subscription. By default MQTTClientWrapper packs as many subscriptions as possible into a
        single subscribe message, so by default child only receives a single suback for all subscriptions.
        So that we can test (awaiting_setup_and_peer -> mqtt_suback -> awaiting_setup_and_peer) self-loop transition,
        which might occur if we have too many subscriptions for that to be possible, we force the suback response to
        be split into multiple messages.

        In practice these might be corner cases that rarely or never occur, since by default all subacks will come and
        one message and we should not receive any messages before subscribing.
        """
        async with self.CTH(add_child=True, verbose=True) as h:
            child = h.child
            stats = child.stats.link(child.upstream_client)
            comm_event_counts = stats.comm_event_counts
            link = child._link_states.link(child.upstream_client)

            # unstarted child
            assert stats.num_received == 0
            assert link.state == StateName.not_started

            # start child
            child.split_client_subacks(child.upstream_client)
            child.pause_subacks()
            h.start_child()
            await await_for(
                lambda: len(child.pending_subacks) == 3,
                3,
                "ERROR waiting link reconnect",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer
            assert not link.active_for_recv()
            assert not link.active()
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert len(stats.comm_events) == 1
            for comm_event in stats.comm_events:
                assert comm_event.MessageId in child._event_persister

            # Allow one suback at a time to arrive
            # suback 1/3
            # (mqtt_suback -> awaiting_setup_and_peer)
            num_subacks = child.stats.num_received_by_type["mqtt_suback"]
            child.release_subacks(1)
            exp_subacks = num_subacks + 1
            await await_for(
                lambda: child.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
                1,
                f"ERROR waiting mqtt_suback {exp_subacks} (1/3)",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer

            # suback 2/3
            # (mqtt_suback -> awaiting_setup_and_peer)
            child.release_subacks(1)
            exp_subacks += 1
            await await_for(
                lambda: child.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
                1,
                f"ERROR waiting mqtt_suback {exp_subacks} (2/3)",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer

            # suback 3/3
            # (mqtt_suback -> awaiting_peer)
            child.release_subacks(1)
            exp_subacks += 1
            await await_for(
                lambda: child.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
                1,
                f"ERROR waiting mqtt_suback {exp_subacks} (3/3)",
                err_str_f=child.summary_str
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
                assert comm_event.MessageId in child._event_persister

            # (message_from_peer -> awaiting_setup)
            # Tell client we lost comm
            child.pause_subacks()
            child._mqtt_clients.clients[child.upstream_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            await await_for(
                lambda: len(child.pending_subacks) == 3,
                3,
                "ERROR waiting suback pending",
                err_str_f=child.summary_str
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
                assert comm_event.MessageId in child._event_persister

            # Allow one suback at a time to arrive
            # (Not strictly necessary, since message receiving code does not check if the source topic suback
            #  has arrived).
            num_subacks = child.stats.num_received_by_type["mqtt_suback"]
            child.release_subacks(1)
            exp_subacks = num_subacks + 1
            await await_for(
                lambda: child.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
                1,
                f"ERROR waiting mqtt_suback {exp_subacks} (1/3)",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer

            # Start the parent, wait for it to send us a message, which will
            # transition us into awaiting_setup
            h.add_parent()
            h.start_parent()
            await await_for(
                lambda: link.in_state(StateName.awaiting_setup),
                3,
                "ERROR waiting suback pending",
                err_str_f=child.summary_str
            )
            assert not link.active_for_send()
            assert not link.active_for_recv()
            assert not link.active()
            assert link.state == StateName.awaiting_setup
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
            assert len(stats.comm_events) == 4

    # @pytest.mark.skip

    @pytest.mark.asyncio
    async def test_awaiting_setup2__(self, request):
        """
        Test awaiting_setup (corner state):
         (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
         (awaiting_setup -> mqtt_suback -> awaiting_setup)
         (awaiting_setup -> mqtt_suback -> active)
         (awaiting_setup -> message_from_peer -> awaiting_setup)
         (awaiting_setup -> disconnected -> connecting)
        Force 1 suback per subscription. By default MQTTClientWrapper packs as many subscriptions as possible into a
        single subscribe message, so by default child only receives a single suback for all subscriptions.
        So that we can test (awaiting_setup_and_peer -> mqtt_suback -> awaiting_setup_and_peer) self-loop transition,
        which might occur if we have too many subscriptions for that to be possible, we force the suback response to
        be split into multiple messages.

        In practice these might be corner cases that rarely or never occur, since by default all subacks will come and
        one message and we should not receive any messages before subscribing.
        """
        async with self.CTH(add_child=True, add_parent=True, verbose=True) as h:
            child = h.child
            child_subscriptions = child.mqtt_subscriptions(child.upstream_client)
            if len(child_subscriptions) < 2:
                warnings.warn(
                    f"Skipping <{request.node.name}> because configured child proactor <{child.name}> "
                    f"has < 2 subscriptions. Subscriptions: {child_subscriptions}"
                )
                return
            stats = child.stats.link(child.upstream_client)
            comm_event_counts = stats.comm_event_counts
            link = child._link_states.link(child.upstream_client)

            # unstarted child
            assert stats.num_received == 0
            assert link.state == StateName.not_started

            # start child
            # (not_started -> started -> connecting)
            # (connecting -> connected -> awaiting_setup_and_peer)
            child.split_client_subacks(child.upstream_client)
            child.pause_subacks()
            h.start_child()
            await await_for(
                lambda: len(child.pending_subacks) == 3,
                3,
                "ERROR waiting link reconnect",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer
            assert not link.active_for_recv()
            assert not link.active()
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 1
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 0
            assert len(stats.comm_events) == 1
            for comm_event in stats.comm_events:
                assert comm_event.MessageId in child._event_persister

            # Allow one suback at a time to arrive
            # (Not strictly necessary, since message receiving code does not check if the source topic suback
            #  has arrived).
            num_subacks = child.stats.num_received_by_type["mqtt_suback"]
            child.release_subacks(1)
            exp_subacks = num_subacks + 1
            await await_for(
                lambda: child.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
                1,
                f"ERROR waiting mqtt_suback {exp_subacks} (1/3)",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer

            # (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
            # Start the parent, wait for it to send us a message, which will
            # transition us into awaiting_setup
            h.start_parent()

            await await_for(
                lambda: link.in_state(StateName.awaiting_setup),
                3,
                "ERROR waiting suback pending",
                err_str_f=child.summary_str
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
            child.release_subacks(1)
            exp_subacks = num_subacks + 1
            await await_for(
                lambda: child.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
                1,
                f"ERROR waiting mqtt_suback {exp_subacks} (2/3)",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup

            # (awaiting_setup -> message_from_peer -> awaiting_setup)
            # Receive another message from peer, remaining in awaiting_setup
            parent = h.parent
            dbg_topic = MQTTTopic.encode("gw", parent.publication_name, DBGPayload.__fields__["TypeName"].default)
            assert stats.num_received_by_topic[dbg_topic] == 0
            parent.send_dbg_to_peer()
            await await_for(
                lambda: stats.num_received_by_topic[dbg_topic] == 1,
                1,
                "ERROR waiting for dbg message",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup

            # (awaiting_setup -> disconnected -> connecting)
            # Tell client we lost comm
            child.pending_subacks.clear()
            child.pause_subacks()
            child._mqtt_clients.clients[child.upstream_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            await await_for(
                lambda: len(child.pending_subacks) == 3,
                3,
                "ERROR waiting suback pending",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer
            assert comm_event_counts["gridworks.event.comm.mqtt.connect"] == 2
            assert comm_event_counts["gridworks.event.comm.mqtt.fully_subscribed"] == 0
            assert comm_event_counts["gridworks.event.comm.mqtt.disconnect"] == 1
            assert len(stats.comm_events) == 3
            for comm_event in stats.comm_events:
                assert comm_event.MessageId in child._event_persister

            # Allow one suback at a time to arrive
            # (Not strictly necessary, since message receiving code does not check if the source topic suback
            #  has arrived).
            num_subacks = child.stats.num_received_by_type["mqtt_suback"]
            child.release_subacks(1)
            exp_subacks = num_subacks + 1
            await await_for(
                lambda: child.stats.num_received_by_type["mqtt_suback"] == exp_subacks,
                1,
                f"ERROR waiting mqtt_suback {exp_subacks} (1/3)",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_setup_and_peer

            # (awaiting_setup_and_peer -> message_from_peer -> awaiting_setup)
            # Force parent to restore comm, delivering a message, sending us to awaiting_setup
            parent._mqtt_clients.clients[parent.primary_peer_client]._client._loop_rc_handle(MQTT_ERR_CONN_LOST)
            await await_for(
                lambda: link.in_state(StateName.awaiting_setup),
                3,
                f"ERROR waiting for message from peer",
                err_str_f=child.summary_str
            )

            # (awaiting_setup -> mqtt_suback -> active)
            # Release all subacks, allowing child to go active
            child.release_subacks()
            await await_for(
                lambda: link.in_state(StateName.active),
                1,
                f"ERROR waiting for active",
                err_str_f=child.summary_str
            )

    @pytest.mark.asyncio
    async def test_response_timeout2(self):
        """
        Test:
            (awaiting_peer -> response_timeout -> awaiting_peer)
            (active -> response_timeout -> awaiting_peer)
        """

        async with self.CTH(add_child=True, add_parent=True, verbose=True) as h:
            child = h.child
            link = child._link_states.link(child.upstream_client)
            stats = child.stats.link(child.upstream_client)
            parent = h.parent
            parent_link = parent._link_states.link(parent.primary_peer_client)

            # Timeout while awaiting setup
            # (awaiting_peer -> response_timeout -> awaiting_peer)

            # start parent
            parent.pause_acks()
            h.start_parent()
            await await_for(
                lambda: parent_link.in_state(StateName.awaiting_peer),
                3,
                "ERROR waiting for parent to connect to broker",
                err_str_f=parent.summary_str
            )

            # start child
            child.ack_timeout_seconds = .1
            assert stats.timeouts == 0
            h.start_child()
            await await_for(
                lambda: link.in_state(StateName.awaiting_peer),
                3,
                "ERROR waiting for child to connect to broker",
                err_str_f=parent.summary_str
            )
            # (awaiting_peer -> response_timeout -> awaiting_peer)
            await await_for(
                lambda: stats.timeouts > 0,
                1,
                "ERROR waiting for child to timeout",
                err_str_f=parent.summary_str
            )
            assert link.state == StateName.awaiting_peer
            assert child._event_persister.num_pending > 0

            # release the hounds
            # (awaiting_peer -> message_from_peer -> active)
            parent.release_acks()
            await await_for(
                lambda: link.in_state(StateName.active),
                1,
                "ERROR waiting for parent to restore link #1",
                err_str_f=parent.summary_str
            )
            # wait for all events to be acked
            await await_for(
                lambda: child._event_persister.num_pending == 0,
                1,
                "ERROR waiting for events to be acked",
                err_str_f=child.summary_str
            )

            # Timeout while active
            # (active -> response_timeout -> awaiting_peer)
            parent.pause_acks()
            child.ping_peer()
            exp_timeouts = stats.timeouts + len(child._acks)
            await await_for(
                lambda: stats.timeouts == exp_timeouts,
                1,
                "ERROR waiting for child to timeout",
                err_str_f=child.summary_str
            )
            assert link.state == StateName.awaiting_peer
            assert child._event_persister.num_pending > 0
            await await_for(
                lambda: len(parent.needs_ack) == 2,
                1,
                "ERROR waiting for child to timeout",
                err_str_f=child.summary_str
            )

            # (awaiting_peer -> message_from_peer -> active)
            parent.release_acks()
            await await_for(
                lambda: link.in_state(StateName.active),
                1,
                "ERROR waiting for parent to restore link #1",
                err_str_f=parent.summary_str
            )

    # @pytest.mark.skip
    @pytest.mark.asyncio
    async def test_ping2(self):
        """
        Test:
            ping sent peridoically if no messages sent
            ping not sent if messages are sent
            ping restores comm
        """
        child_settings = self.CTH.child_settings_t()
        parent_settings = self.CTH.parent_settings_t()
        child_settings.mqtt_link_poll_seconds = parent_settings.mqtt_link_poll_seconds = .1
        async with self.CTH(
            add_child=True,
            add_parent=True,
            child_settings=child_settings,
            parent_settings=parent_settings,
            verbose=True,
        ) as h:
            parent = h.parent
            parent_stats = parent.stats.link(parent.primary_peer_client)
            parent_ping_topic = MQTTTopic.encode("gw", parent.publication_name, "gridworks-ping")

            child = h.child
            child.suppress_status = True
            child.ack_timeout_seconds = .1
            link = child._link_states.link(child.upstream_client)
            stats = child.stats.link(child.upstream_client)
            child_ping_topic = MQTTTopic.encode("gw", child.publication_name, "gridworks-ping")

            # start parent and child
            h.start_parent()
            h.start_child()
            await await_for(
                lambda: link.in_state(StateName.active),
                3,
                "ERROR waiting for child active",
                err_str_f=child.summary_str
            )

            # Test that ping sent peridoically if no messages sent
            start_pings_from_parent = stats.num_received_by_topic[parent_ping_topic]
            start_pings_from_child = parent_stats.num_received_by_topic[child_ping_topic]
            start_messages_from_parent = stats.num_received
            start_messages_from_child = parent_stats.num_received
            wait_seconds = .5
            await asyncio.sleep(wait_seconds)
            pings_from_parent = stats.num_received_by_topic[parent_ping_topic] - start_pings_from_parent
            pings_from_child = parent_stats.num_received_by_topic[child_ping_topic] - start_pings_from_child
            messages_from_parent = stats.num_received - start_messages_from_parent
            messages_from_child = parent_stats.num_received - start_messages_from_child
            exp_pings_nominal = wait_seconds / parent.settings.mqtt_link_poll_seconds
            err_str = (
                f"pings_from_parent: {pings_from_parent}\n"
                f"messages_from_parent: {messages_from_parent}\n"
                f"pings_from_child: {pings_from_child}\n"
                f"messages_from_child: {messages_from_child}\n"
                f"exp_pings_nominal: {exp_pings_nominal}\n"
            )
            assert (pings_from_child + pings_from_parent) >= exp_pings_nominal, err_str
            assert messages_from_child >= exp_pings_nominal, err_str
            assert messages_from_parent >= exp_pings_nominal, err_str

            # Test that ping not sent peridoically if messages are sent
            start_pings_from_parent = stats.num_received_by_topic[parent_ping_topic]
            start_pings_from_child = parent_stats.num_received_by_topic[child_ping_topic]
            start_messages_from_parent = stats.num_received
            start_messages_from_child = parent_stats.num_received
            reps = 50
            for _ in range(reps):
                parent.send_dbg_to_peer()
                await asyncio.sleep(.01)
            pings_from_parent = stats.num_received_by_topic[parent_ping_topic] - start_pings_from_parent
            pings_from_child = parent_stats.num_received_by_topic[child_ping_topic] - start_pings_from_child
            messages_from_parent = stats.num_received - start_messages_from_parent
            messages_from_child = parent_stats.num_received - start_messages_from_child
            exp_pings_nominal = 2
            err_str = (
                f"pings_from_parent: {pings_from_parent}\n"
                f"messages_from_parent: {messages_from_parent}\n"
                f"pings_from_child: {pings_from_child}\n"
                f"messages_from_child: {messages_from_child}\n"
                f"exp_pings_nominal: {exp_pings_nominal}\n"
            )
            print(err_str)
            print(parent.summary_str())
            assert pings_from_parent <= exp_pings_nominal, err_str
            assert pings_from_child <= exp_pings_nominal, err_str
            assert messages_from_parent >= reps, err_str
            assert messages_from_child >= 2 * reps, err_str

            parent.pause_acks()
            await await_for(
                lambda: link.in_state(StateName.awaiting_peer),
                1,
                "ERROR waiting for for parent to be slow",
                err_str_f=child.summary_str
            )
            parent.release_acks(clear=True)
            await await_for(
                lambda: link.in_state(StateName.active),
                1,
                "ERROR waiting for parent to respond",
                err_str_f=child.summary_str
            )
