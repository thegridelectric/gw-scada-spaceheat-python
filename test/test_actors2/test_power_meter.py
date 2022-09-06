import logging
import typing

import pytest

import actors2
from actors.utils import gw_mqtt_topic_encode
from actors2 import Nodes, Scada2
from actors2.power_meter import PowerMeterDriverThread, PowerMeter, DriverThreadSetupHelper
from config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.sh_node import ShNode
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import GridworksSimPm1_PowerMeterDriver
from load_house import load_all
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from test.fragment_runner import ProtocolFragment, AsyncFragmentRunner
from test.utils import await_for


def test_power_meter_small():
    settings = ScadaSettings()
    load_all(settings.world_root_alias)
    scada = Scada2(ShNode.by_alias["a.s"], settings)

    # Raise exception if initiating node is anything except the unique power meter node
    with pytest.raises(Exception):
        PowerMeter(node=ShNode.by_alias["a.s"], services=scada)

    meter = PowerMeter(node=ShNode.by_alias["a.m"], services=scada)
    assert isinstance(meter._sync_thread, PowerMeterDriverThread)
    driver_thread: PowerMeterDriverThread = meter._sync_thread
    setup_helper = DriverThreadSetupHelper(meter.node, settings)

    assert set(driver_thread.nameplate_telemetry_value.keys()) == set(
        Nodes.all_power_meter_telemetry_tuples()
    )
    assert set(driver_thread.last_reported_telemetry_value.keys()) == set(
        Nodes.all_power_meter_telemetry_tuples()
    )
    assert set(driver_thread.latest_telemetry_value.keys()) == set(Nodes.all_power_meter_telemetry_tuples())
    assert set(driver_thread.eq_reporting_config.keys()) == set(Nodes.all_power_meter_telemetry_tuples())
    assert set(driver_thread._last_sampled_s.keys()) == set(Nodes.all_power_meter_telemetry_tuples())

    # Only get resistive heater nameplate attributes if node role is boost element
    with pytest.raises(Exception):
        setup_helper.get_resistive_heater_nameplate_power_w(ShNode.by_alias["a.tank.temp0"])

    with pytest.raises(Exception):
        setup_helper.get_resistive_heater_nameplate_current_amps(ShNode.by_alias["a.tank.temp0"])

    all_eq_configs = driver_thread.reporting_config.ElectricalQuantityReportingConfigList

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
    assert tt in Nodes.all_power_meter_telemetry_tuples()
    assert driver_thread.last_reported_telemetry_value[tt] is None
    assert driver_thread.latest_telemetry_value[tt] is None

    # If latest_telemetry_value is None, should not report reading
    assert driver_thread.should_report_telemetry_reading(tt) is False
    driver_thread.update_latest_value_dicts()
    assert isinstance(driver_thread.latest_telemetry_value[tt], int)
    assert driver_thread.last_reported_telemetry_value[tt] is None

    # If last_reported_telemetry_value exists, but last_reported is None, should report
    assert driver_thread.should_report_telemetry_reading(tt)
    driver_thread.report_sampled_telemetry_values([tt])

    assert driver_thread.last_reported_telemetry_value[tt] == driver_thread.latest_telemetry_value[tt]

    driver_thread.last_reported_telemetry_value[tt] = driver_thread.latest_telemetry_value[tt]

    assert driver_thread.value_exceeds_async_threshold(tt) is False
    report_threshold_ratio = driver_thread.eq_reporting_config[tt].AsyncReportThreshold
    assert driver_thread.nameplate_telemetry_value[tt] == 18750000
    assert report_threshold_ratio == 0.02
    report_threshold_microamps = driver_thread.nameplate_telemetry_value[tt] * 0.02
    assert report_threshold_microamps == 375000

    driver_thread.latest_telemetry_value[tt] += 374000
    assert driver_thread.value_exceeds_async_threshold(tt) is False

    driver_thread.latest_telemetry_value[tt] += 10000
    assert driver_thread.value_exceeds_async_threshold(tt) is True
    assert driver_thread.should_report_telemetry_reading(tt) is True
    driver_thread.report_sampled_telemetry_values([tt])
    assert driver_thread.last_reported_telemetry_value[tt] == 402000
    assert driver_thread.should_report_telemetry_reading(tt) is False

    assert driver_thread.last_reported_agg_power_w is None
    assert driver_thread.latest_agg_power_w == 0
    assert driver_thread.should_report_aggregated_power()
    driver_thread.report_aggregated_power_w()
    assert not driver_thread.should_report_aggregated_power()

    nameplate_pwr_w_1 = setup_helper.get_resistive_heater_nameplate_power_w(ShNode.by_alias["a.elt1"])
    nameplate_pwr_w_2 = setup_helper.get_resistive_heater_nameplate_power_w(ShNode.by_alias["a.elt2"])
    assert nameplate_pwr_w_1 == 4500
    assert nameplate_pwr_w_2 == 4500
    assert driver_thread.nameplate_agg_power_w == 9000
    power_reporting_threshold_ratio = driver_thread.async_power_reporting_threshold
    assert power_reporting_threshold_ratio == 0.02
    power_reporting_threshold_w = power_reporting_threshold_ratio * driver_thread.nameplate_agg_power_w
    assert power_reporting_threshold_w == 180

    tt = TelemetryTuple(
        AboutNode=ShNode.by_alias["a.elt1"],
        SensorNode=meter.node,
        TelemetryName=TelemetryName.POWER_W,
    )
    driver_thread.latest_telemetry_value[tt] += 100
    assert not driver_thread.should_report_aggregated_power()
    driver_thread.latest_telemetry_value[tt] += 100
    assert driver_thread.should_report_aggregated_power()
    driver_thread.report_aggregated_power_w()
    assert driver_thread.latest_agg_power_w == 200


@pytest.mark.asyncio
async def test_power_meter_periodic_update(tmp_path, monkeypatch):
    """Verify the PowerMeter sends its periodic GtShTelemetryFromMultipurposeSensor message (GsPwr sending is
    _not_ tested here."""

    monkeypatch.chdir(tmp_path)
    logging.basicConfig(level="DEBUG")
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2]

        def get_requested_actors2(self):
            meter_node = ShNode.by_alias["a.m"]
            meter_cac = typing.cast(ElectricMeterComponent, meter_node.component).cac
            monkeypatch.setattr(meter_cac, "update_period_ms", 0)
            self.runner.actors.meter2 = actors2.PowerMeter(
                node=meter_node,
                services=self.runner.actors.scada2,
                settings=ScadaSettings(seconds_per_report=1)
            )
            return [self.runner.actors.meter2]

        async def async_run(self):
            scada = self.runner.actors.scada2

            expected_tts = [
                TelemetryTuple(
                    AboutNode=ShNode.by_alias["a.elt1"],
                    SensorNode=self.runner.actors.meter2.node,
                    TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
                ),
                TelemetryTuple(
                    AboutNode=ShNode.by_alias["a.elt1"],
                    SensorNode=self.runner.actors.meter2.node,
                    TelemetryName=TelemetryName.POWER_W,
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

            # Verify pediodic delivery.
            received_tt_counts = [
                len(scada._data.recent_values_from_multipurpose_sensor[tt]) for tt in expected_tts
            ]
            print(received_tt_counts)
            for received_count, tt in zip(received_tt_counts, expected_tts):
                await await_for(
                    lambda: len(scada._data.recent_values_from_multipurpose_sensor[tt]) > received_count,
                    5,
                    f"wait for PowerMeter periodic update [{tt.TelemetryName}]"
                )

    await AsyncFragmentRunner.async_run_fragment(Fragment)


@pytest.mark.asyncio
async def test_power_meter_aggregate_power_forward(tmp_path, monkeypatch):
    """Verify that when a simulated change in power is generated, Scadd and Atn both get a GsPwr message"""

    monkeypatch.chdir(tmp_path)
    logging.basicConfig(level="DEBUG")
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2, self.runner.actors.atn]

        def get_requested_actors2(self):
            meter_node = ShNode.by_alias["a.m"]
            meter_cac = typing.cast(ElectricMeterComponent, meter_node.component).cac
            monkeypatch.setattr(meter_cac, "update_period_ms", 0)
            self.runner.actors.meter2 = actors2.PowerMeter(
                node=meter_node,
                services=self.runner.actors.scada2,
                settings=ScadaSettings(seconds_per_report=1)
            )
            return [self.runner.actors.meter2]

        async def async_run(self):
            scada = self.runner.actors.scada2
            atn = self.runner.actors.atn
            # TODO: Make better test-public access
            atn_gs_pwr_topic = gw_mqtt_topic_encode(f"{scada._nodes.scada_g_node_alias}/p")

            await await_for(
                lambda: scada._data.latest_total_power_w is not None,
                1,
                "Scada wait for initial GsPwr"
            )

            # TODO: Cleaner test access?
            meter_sync_thread = typing.cast(PowerMeterDriverThread, self.runner.actors.meter2._sync_thread)
            driver = typing.cast(
                GridworksSimPm1_PowerMeterDriver,
                meter_sync_thread.driver
            )

            # Simulate power changes. Verify Scada and Atn get messages for each.
            num_changes = 2
            for i in range(num_changes):
                print(f"Generating GsPwr change {i + 1}/{num_changes}")
                latest_total_power_w = scada._data.latest_total_power_w
                num_atn_gs_pwr = atn.num_received_by_topic[atn_gs_pwr_topic]

                # Simulate a change in aggregate power that should trigger a GsPwr message
                increment = int(
                    meter_sync_thread.async_power_reporting_threshold * meter_sync_thread.nameplate_agg_power_w
                ) + 1
                expected = latest_total_power_w + (increment * scada.GS_PWR_MULTIPLIER * len(Nodes.all_power_tuples()))
                driver.fake_power_w += increment

                # Verify scada gets the message
                await await_for(
                    lambda: scada._data.latest_total_power_w > latest_total_power_w,
                    1,
                    "Scada wait for GsPwr"
                )
                assert scada._data.latest_total_power_w == expected

                # Verify Atn gets the forwarded message
                await await_for(
                    lambda: atn.num_received_by_topic[atn_gs_pwr_topic] > num_atn_gs_pwr,
                    1,
                    "Atn wait for GsPwr"
                )

    await AsyncFragmentRunner.async_run_fragment(Fragment)
