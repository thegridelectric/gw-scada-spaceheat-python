"""
Tests for enum main.auto.event.000 from the GridWorks Type Registry.
"""

from enums import MainAutoEvent


def test_main_auto_event() -> None:
    assert set(MainAutoEvent.values()) == {
        "AtnLinkDead",
        "AtnWantsControl",
        "AutoGoesDormant",
        "AutoWakesUp",
    }

    assert MainAutoEvent.default() == MainAutoEvent.AutoGoesDormant
    assert MainAutoEvent.enum_name() == "main.auto.event"
    assert MainAutoEvent.enum_version() == "000"
