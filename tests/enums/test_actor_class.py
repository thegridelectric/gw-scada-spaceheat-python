"""Tests for schema enum sh.actor.class.000"""
from enums import ActorClass


def test_actor_class() -> None:

    assert set(ActorClass.values()) == set(
        [
            "NoActor",
            "Scada",
            "HomeAlone",
            "BooleanActuator",
            "PowerMeter",
            "Atn",
            "SimpleSensor",
            "MultipurposeSensor",
            "Thermostat",
        ]
    )

    assert ActorClass.default() == ActorClass.NoActor
