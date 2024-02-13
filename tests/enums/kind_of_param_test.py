"""
Tests for enum spaceheat.kind.of.param.000 from the GridWorks Type Registry.
"""
from enums import KindOfParam


def test_kind_of_param() -> None:
    assert set(KindOfParam.values()) == {
        "Other",
        "HardwareLayout",
        "DotEnv",
    }

    assert KindOfParam.default() == KindOfParam.Other
    assert KindOfParam.enum_name() == "spaceheat.kind.of.param"
    assert KindOfParam.enum_version() == "000"

    assert KindOfParam.version("Other") == "000"
    assert KindOfParam.version("HardwareLayout") == "000"
    assert KindOfParam.version("DotEnv") == "000"

    for value in KindOfParam.values():
        symbol = KindOfParam.value_to_symbol(value)
        assert KindOfParam.symbol_to_value(symbol) == value
