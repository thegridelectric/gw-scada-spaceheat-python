from abc import ABC
from enum import auto
from typing import Dict, List

from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError


class Unit(StrEnum):
    """
    Specifies the physical unit of sensed data reported by SCADA

    Choices and descriptions:

      * Unknown:
      * Unitless:
      * W:
      * Celcius:
      * Fahrenheit:
      * Gpm:
      * WattHours:
      * AmpsRms:
      * VoltsRms:
      * Gallons:
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


class UnitGtEnum(SpaceheatUnit100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class UnitMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not UnitGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {UnitMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, unit):
        if not isinstance(unit, Unit):
            raise MpSchemaError(f"{unit} must be of type {Unit}")
        return cls.local_to_gt_dict[unit]

    gt_to_local_dict: Dict[str, Unit] = {
        "00000000": Unit.Unknown,
        "ec972387": Unit.Unitless,
        "f459a9c3": Unit.W,
        "ec14bd47": Unit.Celcius,
        "7d8832f8": Unit.Fahrenheit,
        "b4580361": Unit.Gpm,
        "d66f1622": Unit.WattHours,
        "a969ac7c": Unit.AmpsRms,
        "e5d7555c": Unit.VoltsRms,
        "8e123a26": Unit.Gallons,
    }

    local_to_gt_dict: Dict[Unit, str] = {
        Unit.Unknown: "00000000",
        Unit.Unitless: "ec972387",
        Unit.W: "f459a9c3",
        Unit.Celcius: "ec14bd47",
        Unit.Fahrenheit: "7d8832f8",
        Unit.Gpm: "b4580361",
        Unit.WattHours: "d66f1622",
        Unit.AmpsRms: "a969ac7c",
        Unit.VoltsRms: "e5d7555c",
        Unit.Gallons: "8e123a26",
    }
