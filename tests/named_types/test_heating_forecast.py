"""Tests heating.forecast type, version 000"""

from named_types import HeatingForecast


def test_heating_forecast_generated() -> None:
    d = {
        "Time": [1736812800],
        "AvgPowerKw": [13.2],
        "RswtF": [154.2],
        "RswtDeltaTF": [15],
        "TypeName": "heating.forecast",
        "Version": "000",
    }

    d2 = HeatingForecast.model_validate(d).model_dump(exclude_none=True)

    assert d2 == d
