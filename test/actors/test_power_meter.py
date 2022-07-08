"""Test PowerMeter actor"""

import load_house
from actors.power_meter import PowerMeter
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
    load_house.load_all()
    meter = PowerMeter(node=ShNode.by_alias["a.m"])

    assert list(meter.max_telemetry_value.keys()) == meter.my_telemetry_tuples()
    assert list(meter.prev_telemetry_value.keys()) == meter.my_telemetry_tuples()
    assert list(meter.latest_telemetry_value.keys()) == meter.my_telemetry_tuples()
    assert list(meter.eq_config.keys()) == meter.my_telemetry_tuples()
    assert list(meter._last_sampled_s.keys()) == meter.my_telemetry_tuples()

    all_eq_configs = meter.config.reporting.ElectricalQuantityReportingConfigList
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
    assert tt in meter.my_telemetry_tuples()
    assert meter.latest_telemetry_value[tt] is None
    assert meter.prev_telemetry_value[tt] is None
    meter.update_prev_and_latest_value_dicts()
    assert isinstance(meter.latest_telemetry_value[tt], int)
    meter.update_prev_and_latest_value_dicts()
    assert isinstance(meter.prev_telemetry_value[tt], int)

    assert meter.max_telemetry_value[tt] == 10**7
    meter.prev_telemetry_value[tt] = meter.latest_telemetry_value[tt]
    assert meter.value_exceeds_async_threshold(tt) is False
    meter.latest_telemetry_value[tt] += int(
        0.1 * meter.eq_config[tt].AsyncReportThreshold * meter.max_telemetry_value[tt]
    )
    assert meter.value_exceeds_async_threshold(tt) is False
    assert meter.should_report_telemetry_reading(tt)
    meter.report_sampled_telemetry_values([tt])
    assert meter.should_report_telemetry_reading(tt) is False

    meter.latest_telemetry_value[tt] += int(
        meter.eq_config[tt].AsyncReportThreshold * meter.max_telemetry_value[tt]
    )
    assert meter.value_exceeds_async_threshold(tt) is True
