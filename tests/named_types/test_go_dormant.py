"""Tests go.dormant type, version 000"""

from named_types import GoDormant


def test_go_dormant_generated() -> None:
    d = {
        "FromName": "auto",
        "ToName": "pico-cycler",
        "TriggerId": "dc6c6689-e1b1-4e60-adf9-94db59c7f96a",
        "TypeName": "go.dormant",
        "Version": "000",
    }

    d2 = GoDormant.model_validate(d).model_dump(exclude_none=True)

    assert d2 == d
