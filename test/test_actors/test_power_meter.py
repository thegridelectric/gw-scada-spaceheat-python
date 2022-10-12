"""Test PowerMeter actor"""
import json
import typing
import pytest

import load_house
from actors.power_meter import PowerMeter
from actors.scada import Scada
from config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.hardware_layout import HardwareLayout
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import GridworksSimPm1_PowerMeterDriver
from named_tuples.telemetry_tuple import TelemetryTuple

from test.utils import wait_for, ScadaRecorder, AtnRecorder, flush_all
from actors.utils import gw_mqtt_topic_encode

from drivers.power_meter.unknown_power_meter_driver import UnknownPowerMeterDriver

from schema.enums.make_model.make_model_map import MakeModel
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName
from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import GtElectricMeterCac_Maker

from schema.gt.gt_electric_meter_component.gt_electric_meter_component_maker import (
    GtElectricMeterComponent_Maker,
)

def test_driver_loading():

    # Testing unknown meter driver
    flush_all()
    settings = ScadaSettings()
    with settings.paths.hardware_layout.open() as f:
        layout_dict = json.loads(f.read())
    meter_node_idx = -1
    for i, v in enumerate(layout_dict["ShNodes"]):
        if v["Alias"] == "a.m":
            meter_node_idx = i
            break

    layout_dict["ElectricMeterCacs"][0] = {
        "ComponentAttributeClassId": "c1f17330-6269-4bc5-aa4b-82e939e9b70c",
        "MakeModelGtEnumSymbol": "b6a32d9b",
        "DisplayName": "Unknown Power Meter",
        "LocalCommInterfaceGtEnumSymbol": "829549d1",
        "TypeAlias": "gt.electric.meter.cac.100",
    }
    layout_dict["ElectricMeterComponents"][0] = {
        "ComponentId": "c7d352db-9a86-40f0-9601-d99243719cc5",
        "DisplayName": "Test unknown meter",
        "ComponentAttributeClassId": "c1f17330-6269-4bc5-aa4b-82e939e9b70c",
        "HwUid": "7ec4a224",
        "TypeAlias": "gt.electric.meter.component.100",
    }
    layout_dict["ShNodes"][meter_node_idx] = {
        "Alias": "a.m",
        "RoleGtEnumSymbol": "9ac68b6e",
        "ActorClassGtEnumSymbol": "2ea112b9",
        "DisplayName": "Main Power Meter Little Orange House Test System",
        "ShNodeId": "c9456f5b-5a39-4a48-bb91-742a9fdc461d",
        "ComponentId": "c7d352db-9a86-40f0-9601-d99243719cc5",
        "TypeAlias": "spaceheat.node.gt.100",
    }

    electric_meter_cac = GtElectricMeterCac_Maker.dict_to_dc(layout_dict["ElectricMeterCacs"][0])
    electric_meter_component = GtElectricMeterComponent_Maker.dict_to_dc(layout_dict["ElectricMeterComponents"][0])
    assert electric_meter_component.cac == electric_meter_cac

    layout = HardwareLayout.load_dict(layout_dict)
    meter = PowerMeter("a.m", settings=settings, hardware_layout=layout)
    assert isinstance(meter.driver, UnknownPowerMeterDriver)
    flush_all()

    # Testing faulty meter driver (set to temp sensor)
    with settings.paths.hardware_layout.open() as f:
        layout_dict = json.loads(f.read())

    layout_dict["ElectricMeterCacs"][0] = {
        "ComponentAttributeClassId": "f931a424-317c-4ca7-a712-55aba66070dd",
        "MakeModelGtEnumSymbol": "acd93fb3",
        "DisplayName": "Faulty Power Meter, actually an Adafruit temp sensor",
        "LocalCommInterfaceGtEnumSymbol": "829549d1",
        "TypeAlias": "gt.electric.meter.cac.100",
    }

    layout_dict["ElectricMeterComponents"][0] = {
        "ComponentId": "03f7f670-4896-473f-8dda-521747ee7a2d",
        "DisplayName": "faulty meter, actually an Adafruit temp sensor",
        "ComponentAttributeClassId": "f931a424-317c-4ca7-a712-55aba66070dd",
        "HwUid": "bf0850e1",
        "TypeAlias": "gt.electric.meter.component.100",
    }

    layout_dict["ShNodes"][meter_node_idx] = {
        "Alias": "a.m",
        "RoleGtEnumSymbol": "9ac68b6e",
        "ActorClassGtEnumSymbol": "2ea112b9",
        "DisplayName": "Main Power Meter Little Orange House Test System",
        "ShNodeId": "e07e7632-0f3e-4a8c-badd-c6cb24926d85",
        "ComponentId": "03f7f670-4896-473f-8dda-521747ee7a2d",
        "TypeAlias": "spaceheat.node.gt.100",
    }

    electric_meter_cac = GtElectricMeterCac_Maker.dict_to_dc(layout_dict["ElectricMeterCacs"][0])
    GtElectricMeterComponent_Maker.dict_to_dc(layout_dict["ElectricMeterComponents"][0])
    assert electric_meter_cac.make_model == MakeModel.ADAFRUIT__642

    with pytest.raises(Exception):
        PowerMeter("a.m", settings=settings, hardware_layout=layout)

    flush_all()


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
    layout = load_house.load_all(settings)

    # Raise exception if initiating node is anything except the unique power meter node
    with pytest.raises(Exception):
        PowerMeter("a.s", settings=settings, hardware_layout=layout)

    meter = PowerMeter("a.m", settings=settings, hardware_layout=layout)

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
        meter.get_resistive_heater_nameplate_power_w(layout.node("a.tank.temp0"))

    with pytest.raises(Exception):
        meter.get_resistive_heater_nameplate_current_amps(layout.node("a.tank.temp0"))

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
        AboutNode=layout.node("a.elt1"),
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
    assert meter.nameplate_telemetry_value[tt] == 18750000
    assert report_threshold_ratio == 0.02
    report_threshold_microamps = meter.nameplate_telemetry_value[tt] * 0.02
    assert report_threshold_microamps == 375000

    meter.latest_telemetry_value[tt] += 374000
    assert meter.value_exceeds_async_threshold(tt) is False

    meter.latest_telemetry_value[tt] += 10000
    assert meter.value_exceeds_async_threshold(tt) is True
    assert meter.should_report_telemetry_reading(tt) is True
    meter.report_sampled_telemetry_values([tt])
    assert meter.last_reported_telemetry_value[tt] == 402000
    assert meter.should_report_telemetry_reading(tt) is False

    assert meter.last_reported_agg_power_w is None
    assert meter.latest_agg_power_w == 0
    assert meter.should_report_aggregated_power()
    meter.report_aggregated_power_w()
    assert not meter.should_report_aggregated_power()

    nameplate_pwr_w_1 = meter.get_resistive_heater_nameplate_power_w(layout.node("a.elt1"))
    nameplate_pwr_w_2 = meter.get_resistive_heater_nameplate_power_w(layout.node("a.elt2"))
    assert nameplate_pwr_w_1 == 4500
    assert nameplate_pwr_w_2 == 4500
    assert meter.nameplate_agg_power_w == 9000
    power_reporting_threshold_ratio = meter.settings.async_power_reporting_threshold
    assert power_reporting_threshold_ratio == 0.02
    power_reporting_threshold_w = power_reporting_threshold_ratio * meter.nameplate_agg_power_w
    assert power_reporting_threshold_w == 180

    tt = TelemetryTuple(
        AboutNode=layout.node("a.elt1"),
        SensorNode=meter.node,
        TelemetryName=TelemetryName.POWER_W,
    )
    meter.latest_telemetry_value[tt] += 100
    assert not meter.should_report_aggregated_power()
    meter.latest_telemetry_value[tt] += 100
    assert meter.should_report_aggregated_power()
    meter.report_aggregated_power_w()
    assert meter.latest_agg_power_w == 200


def test_power_meter_periodic_update():
    """Verify the PowerMeter sends its periodic GtShTelemetryFromMultipurposeSensor message (GsPwr sending is
    _not_ tested here."""
    settings = ScadaSettings(seconds_per_report=1)
    layout = load_house.load_all(settings)
    scada = Scada("a.s", settings=settings, hardware_layout=layout)
    meter_node = layout.node("a.m")
    typing.cast(ElectricMeterComponent, meter_node.component).cac.update_period_ms = 0
    meter = PowerMeter(alias=meter_node.alias, settings=settings, hardware_layout=layout)
    actors = [scada, meter]
    expected_tts = [
        TelemetryTuple(
            AboutNode=layout.node("a.elt1"),
            SensorNode=meter.node,
            TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
        ),
        TelemetryTuple(
            AboutNode=layout.node("a.elt1"),
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


def test_power_meter_aggregate_power_forward():
    """Verify that when a simulated change in power is generated, Scadd and Atn both get a GsPwr message"""

    settings = ScadaSettings(seconds_per_report=1)
    layout = load_house.load_all(settings)
    scada = ScadaRecorder("a.s", settings=settings, hardware_layout=layout)
    atn = AtnRecorder("a", settings=settings, hardware_layout=layout)
    meter_node = layout.node("a.m")
    typing.cast(ElectricMeterComponent, meter_node.component).cac.update_period_ms = 0
    meter = PowerMeter(meter_node.alias, settings=settings, hardware_layout=layout)
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
            atn.logger.info(f"Generating GsPwr change {i+1}/{num_changes}")
            num_scada_gs_pwr = scada.num_received_by_topic["a.m/p"]
            atn_gs_pwr_topic = gw_mqtt_topic_encode(f"{scada.scada_g_node_alias}/p")
            num_atn_gs_pwr = atn.num_received_by_topic[atn_gs_pwr_topic]

            # Simulate a change in aggregate power that should trigger a GsPwr message
            typing.cast(
                GridworksSimPm1_PowerMeterDriver,
                meter.driver
            ).fake_power_w += int(meter.settings.async_power_reporting_threshold * meter.nameplate_agg_power_w) + 1

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
