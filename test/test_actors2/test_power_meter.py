import logging
import typing

import pytest

import actors2
from actors.utils import gw_mqtt_topic_encode
from actors2 import Nodes
from actors2.power_meter import PowerMeterDriverThread
from config import ScadaSettings
from data_classes.components.electric_meter_component import ElectricMeterComponent
from data_classes.sh_node import ShNode
from drivers.power_meter.gridworks_sim_pm1__power_meter_driver import GridworksSimPm1_PowerMeterDriver
from named_tuples.telemetry_tuple import TelemetryTuple
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName
from test.fragment_runner import ProtocolFragment, FragmentRunner
from test.utils import await_for


@pytest.mark.asyncio
async def test_power_meter_periodic_update(tmp_path, monkeypatch):
    """Verify the PowerMeter sends its periodic GtShTelemetryFromMultipurposeSensor message (GsPwr sending is
    _not_ tested here."""

    monkeypatch.chdir(tmp_path)
    logging.basicConfig(level="DEBUG")
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)

    class Fragment(ProtocolFragment):
        # TODO: Fragment runner should support or interact with this pattern better
        meter: actors2.PowerMeter

        def __init__(self, runner_: FragmentRunner):
            # TODO: This should probably be easier.
            meter_node = ShNode.by_alias["a.m"]
            meter_cac = typing.cast(ElectricMeterComponent, meter_node.component).cac
            monkeypatch.setattr(meter_cac, "update_period_ms", 0)
            self.meter = actors2.PowerMeter(
                node=meter_node,
                services=runner_.actors.scada2,
                settings=ScadaSettings(seconds_per_report=1)
            )
            super().__init__(runner_)

        def get_requested_actors(self):
            return [self.runner.actors.scada2]

        def get_requested_actors2(self):
            return [self.meter]

        async def async_run(self):
            scada = self.runner.actors.scada2

            expected_tts = [
                TelemetryTuple(
                    AboutNode=ShNode.by_alias["a.elt1"],
                    SensorNode=self.meter.node,
                    TelemetryName=TelemetryName.CURRENT_RMS_MICRO_AMPS,
                ),
                TelemetryTuple(
                    AboutNode=ShNode.by_alias["a.elt1"],
                    SensorNode=self.meter.node,
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

    await FragmentRunner.async_run_fragment(Fragment)


@pytest.mark.asyncio
async def test_power_meter_aggregate_power_forward(tmp_path, monkeypatch):
    """Verify that when a simulated change in power is generated, Scadd and Atn both get a GsPwr message"""

    monkeypatch.chdir(tmp_path)
    logging.basicConfig(level="DEBUG")
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)

    class Fragment(ProtocolFragment):
        meter: actors2.PowerMeter

        def __init__(self, runner_: FragmentRunner):
            meter_node = ShNode.by_alias["a.m"]
            meter_cac = typing.cast(ElectricMeterComponent, meter_node.component).cac
            monkeypatch.setattr(meter_cac, "update_period_ms", 0)
            self.meter = actors2.PowerMeter(
                node=meter_node,
                services=runner_.actors.scada2,
                settings=ScadaSettings(seconds_per_report=1)
            )
            super().__init__(runner_)

        def get_requested_actors(self):
            return [self.runner.actors.scada2, self.runner.actors.atn]

        def get_requested_actors2(self):
            return [self.meter]

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
            meter_sync_thread = typing.cast(PowerMeterDriverThread, self.meter._sync_thread)
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

    await FragmentRunner.async_run_fragment(Fragment)
