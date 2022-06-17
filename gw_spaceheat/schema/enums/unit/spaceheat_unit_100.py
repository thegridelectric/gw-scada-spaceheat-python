"""spaceheat.unit.100 definition"""
from abc import ABC
import enum
from typing import List


class Unit(enum.Enum):
    CELCIUS = "Celcius"
    FAHRENHEIT = "Fahrenheit"
    W = "W"
    UNITLESS = "Unitless"
    

class SpaceheatUnit100GtEnum(ABC):
    symbols: List[str] = ["ec14bd47",
                          "7d8832f8",
                          "f459a9c3",
                          "ec972387",
                          ]
