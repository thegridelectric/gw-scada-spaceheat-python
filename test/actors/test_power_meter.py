"""Test PowerMeter actor"""
import typing

import load_house
import pytest
from actors.power_meter import PowerMeter
from actors.scada import Scada
from config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.sh_node import ShNode
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import GridworksSimPm1_PowerMeterDriver
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from test.utils import wait_for, ScadaRecorder, AtnRecorder


# Refactor this test once we have a simulated relay that can be dispatched with
# the GridWorks Simulated Boolean Actuator and sensed with the GridWorks Simulated Power meter.
# As it stands, appears to be sensitive to timing.
#
# def test_async_power_metering_dag():
#     """Verify power report makes it from meter -> Scada -> AtomicTNode"""
#     logging_on = False
#     load_house.load_all()
#     meter_node = ShNode.by_alias["a.m"]
#     scada_node = ShNode.by_alias["a.s"]
#     atn_node = ShNode.by_alias["a"]
#     atn = AtnRecorder(node=atn_node, logging_on=logging_on)
#     meter = PowerMeter(node=meter_node)
#     scada = Scada(node=scada_node)
#     try:
#         atn.start()
#         atn.terminate_main_loop()
#         atn.main_thread.join()
#         assert atn.total_power_w == 0
#         meter.start()
#         meter.terminate_main_loop()
#         meter.main_thread.join()
#         scada.start()
#         scada.terminate_main_loop()
#         scada.main_thread.join()
#         meter.total_power_w = 2100
#         payload = GsPwr_Maker(power=meter.total_power_w).tuple
#         meter.publish(payload=payload)
#         wait_for(
#             lambda: atn.total_power_w == 2100,
#             10,
#             f"Atn did not receive power message. atn.total_power_w:{atn.total_power_w}  {atn.summary_str()}",
#         )
#     finally:
#         # noinspection PyBroadException
#         try:
#             atn.stop()
#             meter.stop()
#             scada.stop()
#         except:
#             pass


def test_power_meter_small():
    settings = ScadaSettings()
    load_house.load_all(settings.world_root_alias)

    # Raise exception if initiating node is anything except the unique power meter node
    with pytest.raises(Exception):
        PowerMeter(node=ShNode.by_alias["a.s"], settings=settings)

    meter = PowerMeter(node=ShNode.by_alias["a.m"], settings=settings)

    assert set(meter.nameplate_telemetry_value.keys()) == set(
        meter.all_power_meter_telemetry_tuples()
    )
    assert set(meter.last_reported_telemetry_value.keys()) == set(
        meter.all_power_meter_telemetry_tuples()
    )
    assert set(meter.latest_telemetry_value.keys()) == set(meter.all_power_meter_telemetry_tuples())
    assert set(meter.eq_reporting_config.keys()) == set(meter.all_power_meter_telemetry_tuples())
    assert set(meter._last_sampled_s.keys()) == set(meter.all_power_meter_telemetry_tuples())

    # Only get resistive heater nameplate attributes if node role is boost element
    with pytest.raises(Exception):
        meter.get_resistive_heater_nameplate_power_w(ShNode.by_alias["a.tank.temp0"])

    with pytest.raises(Exception):
        meter.get_resistive_heater_nameplate_current_amps(ShNode.by_alias["a.tank.temp0"])

    all_eq_configs = meter.reporting_config.ElectricalQuantityReportingConfigList

    amp_list = list(
        filter(
            lambda x: x.TelemetryName == TelemetryName.CURRENT_RMS_MICRO_AMPS
            and x.ShNodeAlias == "a.elt1",
            all_eq_configs,
        )
    )
    assert (len(amp_list)) == 1
    tt = TelemetryTuple(
        AboutNode=ShNode.by_alias["a.elt1"],
        SensorNode=meter.node,
        TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
    )
    assert tt in meter.all_power_meter_telemetry_tuples()
    assert meter.last_reported_telemetry_value[tt] is None
    assert meter.latest_telemetry_value[tt] is None

    # If latest_telemetry_value is None, should not report reading
    assert meter.should_report_telemetry_reading(tt) is False
    meter.update_latest_value_dicts()
    assert isinstance(meter.latest_telemetry_value[tt], int)
    assert meter.last_reported_telemetry_value[tt] is None

    # If last_reported_telemetry_value exists, but last_reported is None, should report
    assert meter.should_report_telemetry_reading(tt)
    meter.report_sampled_telemetry_values([tt])

    assert meter.last_reported_telemetry_value[tt] == meter.latest_telemetry_value[tt]

    meter.last_reported_telemetry_value[tt] = meter.latest_telemetry_value[tt]

    assert meter.value_exceeds_async_threshold(tt) is False
    report_threshold_ratio = meter.eq_reporting_config[tt].AsyncReportThreshold
    assert report_threshold_ratio == 0.02
    report_threshold_microamps = meter.nameplate_telemetry_value[tt] * 0.02
    assert report_threshold_microamps == 937500

    meter.latest_telemetry_value[tt] += 900000
    assert meter.value_exceeds_async_threshold(tt) is False

    meter.latest_telemetry_value[tt] += 100000
    assert meter.value_exceeds_async_threshold(tt) is True
    meter.report_sampled_telemetry_values([tt])
    assert meter.last_reported_telemetry_value[tt] == 1018000
    assert meter.should_report_telemetry_reading(tt) is False

    assert meter.last_reported_agg_power_w is None
    assert meter.latest_agg_power_w == 0
    assert meter.should_report_aggregated_power()
    meter.report_aggregated_power_w()
    assert not meter.should_report_aggregated_power()

    nameplate_pwr_w_1 = meter.get_resistive_heater_nameplate_power_w(ShNode.by_alias["a.elt1"])
    nameplate_pwr_w_2 = meter.get_resistive_heater_nameplate_power_w(ShNode.by_alias["a.elt2"])
    assert nameplate_pwr_w_1 == 4500
    assert nameplate_pwr_w_2 == 4500
    assert meter.nameplate_agg_power_w == 9000
    power_reporting_threshold_ratio = meter.DEFAULT_ASYNC_REPORTING_THRESHOLD
    assert power_reporting_threshold_ratio == 0.05
    power_reporting_threshold_w = power_reporting_threshold_ratio * meter.nameplate_agg_power_w
    assert power_reporting_threshold_w == 450

    tt = TelemetryTuple(
        AboutNode=ShNode.by_alias["a.elt1"],
        SensorNode=meter.node,
        TelemetryName=TelemetryName.POWER_W,
    )
    meter.latest_telemetry_value[tt] += 300
    assert not meter.should_report_aggregated_power()
    meter.latest_telemetry_value[tt] += 200
    assert meter.should_report_aggregated_power()
    meter.report_aggregated_power_w()
    assert meter.latest_agg_power_w == 500


def test_power_meter_periodic_update(monkeypatch):
    """Verify the PowerMeter sends its periodic GtShTelemetryFromMultipurposeSensor message (GsPwr sending is
    _not_ tested here."""
    settings = ScadaSettings(log_message_summary=True, seconds_per_report=1)
    load_house.load_all(settings.world_root_alias)
    scada = Scada(ShNode.by_alias["a.s"], settings=settings)
    meter_node = ShNode.by_alias["a.m"]
    typing.cast(ElectricMeterComponent, meter_node.component).cac.update_period_ms = 0
    monkeypatch.setattr(typing.cast(ElectricMeterComponent, meter_node.component).cac, "update_period_ms", 0)
    meter = PowerMeter(node=meter_node, settings=settings)
    meter.reporting_sample_period_s = 0
    actors = [scada, meter]
    expected_tts = [
        TelemetryTuple(
            AboutNode=ShNode.by_alias["a.elt1"],
            SensorNode=meter.node,
            TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
        ),
        TelemetryTuple(
            AboutNode=ShNode.by_alias["a.elt1"],
            SensorNode=meter.node,
            TelemetryName=TelemetryName.POWER_W,
        )
    ]
    try:
        # Wait for startup and connection
        for actor in actors:
            actor.start()
        for actor in actors:
            wait_for(actor.client.is_connected, 10, f"{actor.node.alias} is_connected")

        # Wait for at least one reading to be delivered since one is delivered on thread startup.
        for tt in expected_tts:
            wait_for(
                lambda: len(scada.recent_values_from_multipurpose_sensor[tt]) > 0,
                2,
                f"wait for PowerMeter first periodic report, [{tt.TelemetryName}]"
            )

        # Verify pediodic delivery.
        received_tt_counts = [
            len(scada.recent_values_from_multipurpose_sensor[tt]) for tt in expected_tts
        ]
        print(received_tt_counts)
        for received_count, tt in zip(received_tt_counts, expected_tts):
            wait_for(
                lambda: len(scada.recent_values_from_multipurpose_sensor[tt]) > received_count,
                2,
                f"wait for PowerMeter periodic update [{tt.TelemetryName}]"
            )
    finally:
        for actor in actors:
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass


def test_power_meter_aggregate_power_forward(monkeypatch):
    """Verify that when a simulated change in power is generated, Scadd and Atn both get a GsPwr message"""

    settings = ScadaSettings(log_message_summary=True, seconds_per_report=1)
    load_house.load_all(settings.world_root_alias)
    scada = ScadaRecorder(ShNode.by_alias["a.s"], settings=settings)
    atn = AtnRecorder(ShNode.by_alias["a"], settings=settings)
    meter_node = ShNode.by_alias["a.m"]
    typing.cast(ElectricMeterComponent, meter_node.component).cac.update_period_ms = 0
    monkeypatch.setattr(typing.cast(ElectricMeterComponent, meter_node.component).cac, "update_period_ms", 0)
    meter = PowerMeter(node=meter_node, settings=settings)
    meter.reporting_sample_period_s = 0
    actors = [scada, meter, atn]
    try:
        # Wait for startup and connection
        for actor in actors:
            actor.start()
        wait_for(meter.client.is_connected, 10, f"{meter.node.alias} is_connected")
        wait_for(scada.client.is_connected, 10, f"{scada.node.alias} is_connected")
        wait_for(scada.gw_client.is_connected, 10, f"{scada.node.alias} gw_client is_connected")
        wait_for(atn.gw_client.is_connected, 10, f"atn gw_client is_connected")
        wait_for(
            lambda: scada.num_received_by_topic["a.m/p"] > 0,
            1,
            "Scada wait for initial GsPwr"
        )

        # Simulate power changes. Verify Scada and Atn get messages for each.
        num_changes = 2
        for i in range(num_changes):
            print(f"Generating GsPwr change {i+1}/{num_changes}")
            num_scada_gs_pwr = scada.num_received_by_topic["a.m/p"]
            atn_gs_pwr_topic = f"{scada.scada_g_node_alias}/p"
            num_atn_gs_pwr = atn.num_received_by_topic[atn_gs_pwr_topic]

            # Simulate a change in aggregate power that should trigger a GsPwr message
            typing.cast(
                GridworksSimPm1_PowerMeterDriver,
                meter.driver
            ).fake_power_w += int(meter.DEFAULT_ASYNC_REPORTING_THRESHOLD * meter.nameplate_agg_power_w) + 1

            # Verify scada gets the message
            wait_for(
                lambda: scada.num_received_by_topic["a.m/p"] > num_scada_gs_pwr,
                1,
                "Scada wait for GsPwr"
            )

            # Verify Atn gets the forwarded message
            wait_for(
                lambda: atn.num_received_by_topic[atn_gs_pwr_topic] > num_atn_gs_pwr,
                1,
                "Atn wait for GsPwr"
            )
    finally:
        for actor in actors:
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass
