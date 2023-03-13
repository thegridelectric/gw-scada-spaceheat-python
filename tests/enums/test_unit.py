"""Tests for schema enum spaceheat.unit.000"""
from enums import Unit


def test_unit() -> None:

    assert set(Unit.values()) == set(
        [
            "Unknown",
            "Unitless",
            "W",
            "Celcius",
            "Fahrenheit",
            "Gpm",
            "WattHours",
            "AmpsRms",
            "VoltsRms",
            "Gallons",
        ]
    )

    assert Unit.default() == Unit.Unknown
