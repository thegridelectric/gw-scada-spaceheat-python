"""Test PowerMeter actor"""

import load_house
import pytest
from actors.power_meter import PowerMeter
from config import ScadaSettings
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName


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
    assert report_threshold_ratio == 0.05
    report_threshold_microamps = meter.nameplate_telemetry_value[tt] * 0.05
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
