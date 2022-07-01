"""sh.node.role.110 definition"""
import enum
from abc import ABC
from typing import List


class Role(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    BOOST_ELEMENT = "BoostElement"
    PIPE_FLOW_METER = "PipeFlowMeter"
    POWER_METER = "PowerMeter"
    HEATED_SPACE = "HeatedSpace"
    SCADA = "Scada"
    HYDRONIC_PIPE = "HydronicPipe"
    PIPE_TEMP_SENSOR = "PipeTempSensor"
    BASEBOARD_RADIATOR = "BaseboardRadiator"
    RADIATOR_FAN = "RadiatorFan"
    CIRCULATOR_PUMP = "CirculatorPump"
    TANK_WATER_TEMP_SENSOR = "TankWaterTempSensor"
    ROOM_TEMP_SENSOR = "RoomTempSensor"
    DEDICATED_THERMAL_STORE = "DedicatedThermalStore"
    OUTDOOR_TEMP_SENSOR = "OutdoorTempSensor"
    BOOLEAN_ACTUATOR = "BooleanActuator"
    ATN = "Atn"
    HOME_ALONE = "HomeAlone"
    OUTDOORS = "Outdoors"
    #


class ShNodeRole110GtEnum(ABC):
    symbols: List[str] = [
        "99c5f326",
        "ece3b600",
        "9ac68b6e",
        "65725f44",
        "d0afb424",
        "fe3cbdd5",
        "c480f612",
        "05fdd645",
        "6896109b",
        "b0eaf2ba",
        "73308a1f",
        "fec74958",
        "3ecfe9b8",
        "5938bf1f",
        "57b788ee",
        "6ddff83b",
        "863e50d1",
        "dd975b31",
        #
    ]
