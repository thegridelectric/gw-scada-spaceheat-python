
"""Test SimpleSensor actor"""
import logging
import typing

import pytest

import actors2
from data_classes.components.temp_sensor_component import TempSensorComponent
from data_classes.sh_node import ShNode
from test.fragment_runner import ProtocolFragment, AsyncFragmentRunner
from test.utils import await_for


@pytest.mark.asyncio
async def test_simple_sensor_periodic_update(tmp_path, monkeypatch):
    """Verify that SimpleSensor sends its periodic GtTelemetry message."""

    monkeypatch.chdir(tmp_path)
    logging.basicConfig(level="DEBUG")
    debug_logs_path = tmp_path / "output/debug_logs"
    debug_logs_path.mkdir(parents=True, exist_ok=True)

    class Fragment(ProtocolFragment):

        def get_requested_actors(self):
            return [self.runner.actors.scada2]

        def get_requested_actors2(self):
            thermo_node = ShNode.by_alias["a.tank.temp0"]
            # Artificially speed up the test by telling the SimpleSensor to report every second
            # and telling it's driver that the read time is .01 ms.
            # Note: The read delay can *still* be 1 second because the times compared are cast to floats.
            thermo_node.reporting_sample_period_s = 0
            typing.cast(TempSensorComponent, thermo_node.component).cac.typical_response_time_ms = .01
            self.runner.actors.thermo2 = actors2.SimpleSensor(
                node=thermo_node,
                services=self.runner.actors.scada2,
            )
            return [self.runner.actors.thermo2]

        async def async_run(self):
            scada = self.runner.actors.scada2
            thermo = self.runner.actors.thermo2
            simple_sensor_reports = len(scada._data.recent_simple_values[thermo.node])
            # Wait for at least one reading to be delivered since one is delivered on thread startup.
            await await_for(
                lambda: len(scada._data.recent_simple_values[thermo.node]) > 0,
                2,
                "wait for SimpleSensor first report"
            )
            # Verify pediodic delivery.
            simple_sensor_reports = len(scada._data.recent_simple_values[thermo.node])
            await await_for(
                lambda: len(scada._data.recent_simple_values[thermo.node]) > simple_sensor_reports,
                2,
                "wait for SimpleSensor periodic update"
            )

    await AsyncFragmentRunner.async_run_fragment(Fragment)
