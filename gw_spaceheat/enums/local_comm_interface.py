""" Enum with TypeName local.comm.interface, Version 000"""
from enum import auto
from typing import List

from fastapi_utils.enums import StrEnum


class LocalCommInterface(StrEnum):
    """
    Categorization of in-house comm mechanisms for SCADA

    Name (EnumSymbol, Version): description

      * UNKNOWN (00000000, 000):
      * I2C (9ec8bc49, 000):
      * ETHERNET (c1e7a955, 000):
      * ONEWIRE (ae2d4cd8, 000):
      * RS485 (a6a4ac9f, 000):
      * SIMRABBIT (efc144cd, 000):
      * WIFI (46ac6589, 000):
      * ANALOG_4_20_MA (653c73b8, 000):
      * RS232 (0843a726, 000):
    """

    UNKNOWN = auto()
    I2C = auto()
    ETHERNET = auto()
    ONEWIRE = auto()
    RS485 = auto()
    SIMRABBIT = auto()
    WIFI = auto()
    ANALOG_4_20_MA = auto()
    RS232 = auto()

    @classmethod
    def default(cls) -> "LocalCommInterface":
        """
        Returns default value UNKNOWN
        """
        return cls.UNKNOWN

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]
