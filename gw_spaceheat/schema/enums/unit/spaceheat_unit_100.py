"""spaceheat.unit.100 definition"""
import enum
from abc import ABC
from typing import List


class Unit(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    UNKNOWN = "Unknown"
    UNITLESS = "Unitless"
    W = "W"
    CELCIUS = "Celcius"
    FAHRENHEIT = "Fahrenheit"
    GPM = "Gpm"
    WATT_HOURS = "WattHours"
    AMPS_RMS = "AmpsRms"
    VOLTS_RMS = "VoltsRms"
    GALLONS = "Gallons"


class SpaceheatUnit100GtEnum(ABC):
    symbols: List[str] = [
        "00000000",
        "ec972387",
        "f459a9c3",
        "ec14bd47",
        "7d8832f8",
        "b4580361",
        "d66f1622",
        "a969ac7c",
        "e5d7555c",
        "8e123a26",
    ]
