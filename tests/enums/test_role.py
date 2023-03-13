"""Tests for schema enum sh.node.role.000"""
from enums import Role


def test_role() -> None:

    assert set(Role.values()) == set(
        [
            "Unknown",
            "Scada",
            "RoomTempSensor",
            "OutdoorTempSensor",
            "PipeFlowMeter",
            "HeatedSpace",
            "HydronicPipe",
            "BaseboardRadiator",
            "RadiatorFan",
            "CirculatorPump",
            "MultiChannelAnalogTempSensor",
            "Outdoors",
            "HomeAlone",
            "Atn",
            "PowerMeter",
            "BoostElement",
            "BooleanActuator",
            "DedicatedThermalStore",
            "TankWaterTempSensor",
            "PipeTempSensor",
        ]
    )

    assert Role.default() == Role.Unknown
