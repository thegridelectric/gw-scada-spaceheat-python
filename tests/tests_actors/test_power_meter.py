import argparse
import asyncio
import logging
import typing

from gwproto.data_classes.hardware_layout import HardwareLayout
from tests.utils.fragment_runner import AsyncFragmentRunner
from tests.utils.fragment_runner import ProtocolFragment
from gwproactor_test import await_for
from gwproactor_test.certs import uses_tls
from gwproactor_test.certs import copy_keys

import actors
import pytest
from actors import Scada
from actors.power_meter import DriverThreadSetupHelper
from actors.power_meter import PowerMeter
from actors.power_meter import PowerMeterDriverThread
from actors.config import ScadaSettings
from gwproto.data_classes.components.electric_meter_component import ElectricMeterComponent
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import (
    GridworksSimPm1_PowerMeterDriver,
)
from gwproactor.config import LoggerLevels
from gwproactor.config import LoggingSettings
from gwproto.data_classes.telemetry_tuple import TelemetryTuple
from gwproto.enums import TelemetryName
from gwproto.messages import PowerWatts

def test_power_meter_small():
    settings = ScadaSettings()
    if uses_tls(settings):
        copy_keys("scada", settings)
    settings.paths.mkdirs()
    layout = HardwareLayout.load(settings.paths.hardware_layout)
    scada = Scada("a.s", settings, layout)
    # Raise exception if initiating node is anything except the unique power meter node
    with pytest.raises(Exception):
        PowerMeter("a.s", services=scada)

    meter = PowerMeter("a.m", services=scada)
    assert isinstance(meter._sync_thread, PowerMeterDriverThread)
    driver_thread: PowerMeterDriverThread = meter._sync_thread
    driver_thread.set_async_loop(asyncio.new_event_loop(), asyncio.Queue())
    setup_helper = DriverThreadSetupHelper(meter.node, settings, layout)

    assert set(driver_thread.nameplate_telemetry_value.keys()) == set(
        layout.all_power_meter_telemetry_tuples
    )
    assert set(driver_thread.last_reported_telemetry_value.keys()) == set(
        layout.all_power_meter_telemetry_tuples
    )
    assert set(driver_thread.latest_telemetry_value.keys()) == set(layout.all_power_meter_telemetry_tuples)
    assert set(driver_thread.eq_reporting_config.keys()) == set(layout.all_power_meter_telemetry_tuples)
    assert set(driver_thread._last_sampled_s.keys()) == set(layout.all_power_meter_telemetry_tuples)



    all_eq_configs = driver_thread.reporting_config.ElectricalQuantityReportingConfigList

    amp_list = list(
        filter(
            lambda x: x.TelemetryName == TelemetryName.CurrentRmsMicroAmps
            and x.AboutNodeName == "a.elt1",
            all_eq_configs,
        )
    )
    assert (len(amp_list)) == 1
    tt_1 = TelemetryTuple(
        AboutNode=layout.node("a.elt1"),
        SensorNode=meter.node,
        TelemetryName=TelemetryName.CurrentRmsMicroAmps,
    )
    assert tt_1 in layout.all_power_meter_telemetry_tuples
    assert driver_thread.last_reported_telemetry_value[tt_1] is None
    assert driver_thread.latest_telemetry_value[tt_1] is None

    # If latest_telemetry_value is None, should not report reading
    assert driver_thread.should_report_telemetry_reading(tt_1) is False
    driver_thread.update_latest_value_dicts()
    assert isinstance(driver_thread.latest_telemetry_value[tt_1], int)
    assert driver_thread.last_reported_telemetry_value[tt_1] is None

    # If last_reported_telemetry_value exists, but last_reported is None, should report
    assert driver_thread.should_report_telemetry_reading(tt_1)
    driver_thread.report_sampled_telemetry_values([tt_1])

    assert driver_thread.last_reported_telemetry_value[tt_1] == driver_thread.latest_telemetry_value[tt_1]

    driver_thread.last_reported_telemetry_value[tt_1] = driver_thread.latest_telemetry_value[tt_1]

    assert driver_thread.value_exceeds_async_threshold(tt_1) is False
    report_threshold_ratio = driver_thread.eq_reporting_config[tt_1].AsyncReportThreshold
    assert driver_thread.nameplate_telemetry_value[tt_1] == 18750000
    assert report_threshold_ratio == 0.02
    report_threshold_microamps = driver_thread.nameplate_telemetry_value[tt_1] * 0.02
    assert report_threshold_microamps == 375000

    driver_thread.latest_telemetry_value[tt_1] += 374000
    assert driver_thread.value_exceeds_async_threshold(tt_1) is False

    driver_thread.latest_telemetry_value[tt_1] += 10000
    assert driver_thread.value_exceeds_async_threshold(tt_1) is True
    assert driver_thread.should_report_telemetry_reading(tt_1) is True
    driver_thread.report_sampled_telemetry_values([tt_1])
    assert driver_thread.last_reported_telemetry_value[tt_1] == 402000
    assert driver_thread.should_report_telemetry_reading(tt_1) is False

    assert driver_thread.last_reported_agg_power_w is None
    assert driver_thread.latest_agg_power_w == 0
    assert driver_thread.should_report_aggregated_power()
    driver_thread.report_aggregated_power_w()
    assert not driver_thread.should_report_aggregated_power()

    pwr_1 = TelemetryTuple(
        AboutNode=layout.node("a.elt1"),
        SensorNode=meter.node,
        TelemetryName=TelemetryName.PowerW
    )
    pwr_2 = TelemetryTuple(
        AboutNode=layout.node("a.elt2"),
        SensorNode=meter.node,
        TelemetryName=TelemetryName.PowerW
    )


    nameplate_pwr_w_1 = driver_thread.eq_reporting_config[pwr_1].NameplateMaxValue
    nameplate_pwr_w_2 = driver_thread.eq_reporting_config[pwr_2].NameplateMaxValue
    assert nameplate_pwr_w_1 == 4500
    assert nameplate_pwr_w_2 == 4500
    assert driver_thread.nameplate_agg_power_w == 9000
    power_reporting_threshold_ratio = driver_thread.async_power_reporting_threshold
    assert power_reporting_threshold_ratio == 0.02
    power_reporting_threshold_w = power_reporting_threshold_ratio * driver_thread.nameplate_agg_power_w
    assert power_reporting_threshold_w == 180

    tt_1 = TelemetryTuple(
        AboutNode=layout.node("a.elt1"),
        SensorNode=meter.node,
        TelemetryName=TelemetryName.PowerW,
    )
    driver_thread.latest_telemetry_value[tt_1] += 100
    assert not driver_thread.should_report_aggregated_power()
    driver_thread.latest_telemetry_value[tt_1] += 100
    assert driver_thread.should_report_aggregated_power()
    driver_thread.report_aggregated_power_w()
    assert driver_thread.latest_agg_power_w == 200


@pytest.mark.asyncio
async def test_power_meter_periodic_update(tmp_path, monkeypatch, request):
    """Verify the PowerMeter sends its periodic GtShTelemetryFromMultipurposeSensor message (PowerWatts sending is
    _not_ tested here."""

    monkeypatch.chdir(tmp_path)

    class Fragment(ProtocolFragment):

        def get_requested_proactors(self):
            return [self.runner.actors.scada]

        def get_requested_actors(self):
            meter_node = self.runner.layout.node("a.m")
            meter_component = typing.cast(ElectricMeterComponent, meter_node.component)
            meter_cac = meter_component.cac
            monkeypatch.setattr(meter_cac, "PollPeriodMs", 0)
            for config in meter_component.gt.ConfigList:
                config.SamplePeriodS = 1
            self.runner.actors.meter = actors.PowerMeter(
                name=meter_node.alias,
                services=self.runner.actors.scada,
                settings=ScadaSettings(seconds_per_report=1)
            )
            return [self.runner.actors.meter]

        async def async_run(self):
            scada = self.runner.actors.scada

            expected_tts = [
                TelemetryTuple(
                    AboutNode=self.runner.layout.node("a.elt1"),
                    SensorNode=self.runner.actors.meter.node,
                    TelemetryName=TelemetryName.PowerW,
                ),
                TelemetryTuple(
                    AboutNode=self.runner.layout.node("a.elt2"),
                    SensorNode=self.runner.actors.meter.node,
                    TelemetryName=TelemetryName.PowerW,
                )
            ]

            # Wait for at least one reading to be delivered since one is delivered on thread startup.
            for tt in expected_tts:
                # TODO: Test-public access for this
                await await_for(
                    lambda: len(scada._data.recent_values_from_multipurpose_sensor[tt]) > 0,
                    5,
                    f"wait for PowerMeter first periodic report, [{tt.TelemetryName}]"
                )

            # Verify periodic delivery.
            received_tt_counts = [
                len(scada._data.recent_values_from_multipurpose_sensor[tt]) for tt in expected_tts
            ]
            scada._logger.info(received_tt_counts)
            for received_count, tt in zip(received_tt_counts, expected_tts):
                await await_for(
                    lambda: len(scada._data.recent_values_from_multipurpose_sensor[tt]) > received_count,
                    5,
                    f"wait for PowerMeter periodic update [{tt.TelemetryName}]"
                )

    await AsyncFragmentRunner.async_run_fragment(Fragment, args=argparse.Namespace(verbose=True), tag=request.node.name)


@pytest.mark.asyncio
async def test_power_meter_aggregate_power_forward(tmp_path, monkeypatch, request):
    """Verify that when a simulated change in power is generated, Scadd and Atn both get a PowerWatts message"""

    monkeypatch.chdir(tmp_path)
    settings = ScadaSettings(
        logging=LoggingSettings(
            base_log_level=logging.DEBUG,
            levels=LoggerLevels(
                message_summary=logging.DEBUG
            )
        )
    )

    class Fragment(ProtocolFragment):

        def get_requested_proactors(self):
            return [self.runner.actors.scada, self.runner.actors.atn]

        def get_requested_actors(self):
            meter_node = self.runner.layout.node("a.m")
            meter_component = typing.cast(ElectricMeterComponent, meter_node.component)
            for config in meter_component.gt.ConfigList:
                config.SamplePeriodS = 1
            meter_cac = meter_component.cac
            monkeypatch.setattr(meter_cac, "PollPeriodMs", 0)
            self.runner.actors.meter = actors.PowerMeter(
                name=meter_node.alias,
                services=self.runner.actors.scada,
                settings=ScadaSettings(seconds_per_report=1)
            )
            return [self.runner.actors.meter]

        async def async_run(self):
            scada = self.runner.actors.scada
            atn = self.runner.actors.atn
            await await_for(
                lambda: scada._data.latest_total_power_w is not None,
                1,
                "Scada wait for initial PowerWatts"
            )

            # TODO: Cleaner test access?
            meter_sync_thread = typing.cast(PowerMeterDriverThread, self.runner.actors.meter._sync_thread)
            driver = typing.cast(
                GridworksSimPm1_PowerMeterDriver,
                meter_sync_thread.driver
            )

            # Simulate power changes. Verify Scada and Atn get messages for each.
            num_changes = 5
            for i in range(num_changes):
                scada._logger.info(f"Generating PowerWatts change {i + 1}/{num_changes}")
                latest_total_power_w = scada._data.latest_total_power_w
                num_atn_power_watts = atn.stats.num_received_by_type[PowerWatts.model_fields['TypeName'].default]

                # Simulate a change in aggregate power that should trigger a PowerWatts message
                increment = int(
                    meter_sync_thread.async_power_reporting_threshold * meter_sync_thread.nameplate_agg_power_w
                ) + 1
                expected = latest_total_power_w + (increment * len(self.runner.layout.all_telemetry_tuples_for_agg_power_metering))
                driver.fake_power_w += increment

                # Verify scada gets the message
                await await_for(
                    lambda: scada._data.latest_total_power_w > latest_total_power_w,
                    1,
                    "Scada wait for PowerWatts"
                )
                assert scada._data.latest_total_power_w == expected

                # Verify Atn gets the forwarded message
                await await_for(
                    lambda: atn.stats.num_received_by_type[PowerWatts.model_fields['TypeName'].default] > num_atn_power_watts,
                    1,
                    "Atn wait for PowerWatts",
                    err_str_f=atn.summary_str,
                )

    await AsyncFragmentRunner.async_run_fragment(Fragment, settings=settings, tag=request.node.name)
