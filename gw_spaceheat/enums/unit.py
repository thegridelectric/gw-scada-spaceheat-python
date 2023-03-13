""" Enum with TypeName spaceheat.unit, Version 000"""
from enum import auto
from typing import List

from fastapi_utils.enums import StrEnum


class Unit(StrEnum):
    """
    Specifies the physical unit of sensed data reported by SCADA

    Name (EnumSymbol, Version): description

      * Unknown (00000000, 000):
      * Unitless (ec972387, 000):
      * W (f459a9c3, 000):
      * Celcius (ec14bd47, 000):
      * Fahrenheit (7d8832f8, 000):
      * Gpm (b4580361, 000):
      * WattHours (d66f1622, 000):
      * AmpsRms (a969ac7c, 000):
      * VoltsRms (e5d7555c, 000):
      * Gallons (8e123a26, 000):
    """

    Unknown = auto()
    Unitless = auto()
    W = auto()
    Celcius = auto()
    Fahrenheit = auto()
    Gpm = auto()
    WattHours = auto()
    AmpsRms = auto()
    VoltsRms = auto()
    Gallons = auto()

    @classmethod
    def default(cls) -> "Unit":
        """
        Returns default value Unknown
        """
        return cls.Unknown

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]
