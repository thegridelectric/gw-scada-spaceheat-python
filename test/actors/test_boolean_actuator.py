"""Test BooleanActuator actor"""

import time

import load_house
import pytest
from data_classes.sh_node import ShNode
from schema.gt.gt_dispatch_boolean_local.gt_dispatch_boolean_local_maker import (
    GtDispatchBooleanLocal_Maker,
)

from actors.boolean_actuator import BooleanActuator


def test_boolean_actuator():
    load_house.load_all()
    boost_relay = BooleanActuator(ShNode.by_alias["a.elt1.relay"])

    # test on_message
    # raises error on unrecongized payload
    with pytest.raises(Exception):
        boost_relay.on_message(
            from_node=boost_relay.scada_node(), payload="Not a GtDispatchBooleanLocal"
        )

    scada_dispatch = GtDispatchBooleanLocal_Maker(
        send_time_unix_ms=int(time.time() * 1000),
        from_node_alias=boost_relay.scada_node().alias,
        about_node_alias=boost_relay.node.alias,
        relay_state=0,
    )

    # requires local boolean dispatch to come from scada node
    with pytest.raises(Exception):
        boost_relay.on_message(from_node=ShNode.by_alias["a"], payload=scada_dispatch)

    with pytest.raises(Exception):
        boost_relay.gt_dispatch_boolean_local_received(
            from_node=ShNode.by_alias["a"], payload=scada_dispatch
        )

    # dispatch_relay requires relay_state of 0 or 1:
    with pytest.raises(Exception):
        boost_relay.dispatch_relay(relay_state="On")

    boost_relay.update_and_report_state_change()
    boost_relay._last_sync_report_time_s = int(time.time()) - 400
    assert boost_relay.time_for_sync_report()
    boost_relay.sync_report()

    try:
        boost_relay.start()
        boost_relay.terminate_main_loop()
        boost_relay.main_thread.join()

    finally:
        # noinspection PyBroadException
        try:
            boost_relay.stop()
        except:
            pass
