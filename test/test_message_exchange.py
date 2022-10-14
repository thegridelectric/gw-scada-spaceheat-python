"""An integration test which verifies some of the messages expected to be exchanged after system startup"""

import time
from test.utils import AtnRecorder
from test.utils import EarRecorder
from test.utils import HomeAloneRecorder
from test.utils import ScadaRecorder
from test.utils import wait_for

import load_house
from actors.boolean_actuator import BooleanActuator
from actors.power_meter import PowerMeter
from actors.simple_sensor import SimpleSensor
from actors.utils import gw_mqtt_topic_encode
from config import ScadaSettings
from schema.messages import GtDispatchBoolean_Maker
from schema.messages import GtDispatchBooleanLocal_Maker


def test_message_exchange(tmp_path, monkeypatch):
    """Run various nodes and verify they send each other messages as expected"""
    monkeypatch.chdir(tmp_path)
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)
    settings = ScadaSettings()
    layout = load_house.load_all(settings)
    scada = ScadaRecorder("a.s", settings=settings, hardware_layout=layout)
    atn = AtnRecorder("a", settings=settings, hardware_layout=layout)
    ear = EarRecorder(settings=settings, hardware_layout=layout)
    home_alone = HomeAloneRecorder("a.home", settings=settings, hardware_layout=layout)
    elt_relay = BooleanActuator("a.elt1.relay", settings=settings, hardware_layout=layout)
    meter = PowerMeter("a.m", settings=settings, hardware_layout=layout)
    thermo = SimpleSensor("a.tank.temp0", settings=settings, hardware_layout=layout)
    actors = [scada, atn, ear, home_alone, elt_relay, meter, thermo]

    try:
        for actor in actors:
            actor.start()
        for actor in actors:
            if hasattr(actor, "client"):
                wait_for(
                    actor.client.is_connected,
                    1,
                    tag=f"ERROR waiting for {actor.node.alias} client connect",
                )
            if hasattr(actor, "gw_client"):
                wait_for(
                    actor.gw_client.is_connected,
                    1,
                    "ERROR waiting for gw_client connect",
                )

        home_alone.terminate_main_loop()
        dispatch_on = GtDispatchBooleanLocal_Maker(
            send_time_unix_ms=int(time.time() * 1000),
            from_node_alias=home_alone.node.alias,
            about_node_alias="a.elt1.relay",
            relay_state=1,
        ).tuple
        home_alone.publish(dispatch_on)
        wait_for(lambda: elt_relay.relay_state == 1, 10, f"Relay state {elt_relay.relay_state}")
        dispatch_off = GtDispatchBooleanLocal_Maker(
            send_time_unix_ms=int(time.time() * 1000),
            from_node_alias=home_alone.node.alias,
            about_node_alias="a.elt1.relay",
            relay_state=0,
        ).tuple
        home_alone.publish(dispatch_off)
        wait_for(lambda: elt_relay.relay_state == 0, 10, f"Relay state {elt_relay.relay_state}")
        scada._scada_atn_fast_dispatch_contract_is_alive_stub = True
        atn.turn_on(layout.node("a.elt1.relay"))
        wait_for(lambda: elt_relay.relay_state == 1, 10, f"Relay state {elt_relay.relay_state}")
        atn.status()
        wait_for(
            lambda: atn.snapshot_received > 0, 10, f"cli_resp_received == 0 {atn.summary_str()}"
        )

        wait_for(
            lambda: len(ear.num_received_by_topic) > 0, 10, f"ear receipt. {ear.summary_str()}"
        )

        topic = gw_mqtt_topic_encode(f"{scada.atn_g_node_alias}/{GtDispatchBoolean_Maker.type_alias}")
        print(topic)
        wait_for(
            lambda: ear.num_received_by_topic[topic] > 0, 10, f"ear receipt. {ear.summary_str()}"
        )
        assert ear.num_received_by_topic[topic] > 0

        wait_for(
            lambda: scada.num_received_by_topic["a.elt1.relay/gt.telemetry.110"] > 0,
            10,
            f"scada elt telemetry. {scada.summary_str()}",
        )

        # wait_for(lambda: scada.num_received_by_topic["a.m/p"] > 0, 10, f"scada power. {scada.summary_str()}")
        # This should report after turning on the relay. But that'll take a simulated element
        # that actually turns on and can be read by the simulated power meter

        wait_for(
            lambda: scada.num_received_by_topic["a.tank.temp0/gt.telemetry.110"] > 0,
            10,
            f"scada temperature. {scada.summary_str()}",
        )

        atn.turn_off(layout.node("a.elt1.relay"))
        wait_for(
            lambda: int(elt_relay.relay_state) == 0, 10, f"Relay state {elt_relay.relay_state}"
        )

        scada.send_status()
        wait_for(lambda: atn.status_received > 0, 10, f"atn summary. {atn.summary_str()}")
        wait_for(
            lambda: home_alone.status_received > 0,
            10,
            f"home alone summary. {home_alone.summary_str()}",
        )

    finally:
        for actor in actors:
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass
