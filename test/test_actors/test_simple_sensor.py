"""Test SimpleSensor actor"""
import typing
from test.utils import wait_for

import load_house
from actors.scada import Scada
from actors.simple_sensor import SimpleSensor
from config import ScadaSettings
from data_classes.components.temp_sensor_component import TempSensorComponent


def test_simple_sensor_periodic_update():
    """Verify that SimpleSensor sends its periodic GtTelemetry message."""
    settings = ScadaSettings()
    layout = load_house.load_all(settings)
    scada = Scada("a.s", settings=settings, hardware_layout=layout)
    thermo_node = layout.node("a.tank.temp0")
    # Artificially speed up the test by telling the SimpleSensor to report every second
    # and telling it's driver that the read time is .01 ms.
    # Note: The read delay can *still* be 1 second because the times compared are cast to floats.
    thermo_node.reporting_sample_period_s = 0
    typing.cast(TempSensorComponent, thermo_node.component).cac.typical_response_time_ms = .01
    thermo = SimpleSensor(thermo_node.alias, settings=settings, hardware_layout=layout)
    actors = [scada, thermo]
    try:
        for actor in actors:
            actor.start()
        for actor in actors:
            wait_for(actor.client.is_connected, 10, f"{actor.node.alias} is_connected")
        simple_sensor_reports = len(scada.recent_simple_values[thermo.node])
        # Wait for at least one reading to be delivered since one is delivered on thread startup.
        wait_for(
            lambda: len(scada.recent_simple_values[thermo.node]) > 0,
            2,
            "wait for SimpleSensor first report"
        )
        # Verify pediodic delivery.
        simple_sensor_reports = len(scada.recent_simple_values[thermo.node])
        wait_for(
            lambda: len(scada.recent_simple_values[thermo.node]) > simple_sensor_reports,
            2,
            "wait for SimpleSensor periodic update"
        )
    finally:
        for actor in actors:
            # noinspection PyBroadException
            try:
                actor.stop()
            except:
                pass
