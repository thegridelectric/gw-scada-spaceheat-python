"""spaceheat.unit.100 definition"""
import enum
from abc import ABC
from typing import List


class Unit(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    CELCIUS = "Celcius"
    AMPS_RMS = "AmpsRms"
    GPM = "Gpm"
    FAHRENHEIT = "Fahrenheit"
    W = "W"
    UNITLESS = "Unitless"
    #


class SpaceheatUnit100GtEnum(ABC):
    symbols: List[str] = [
        "ec14bd47",
        "a969ac7c",
        "b4580361",
        "7d8832f8",
        "f459a9c3",
        "ec972387",
        #
    ]
