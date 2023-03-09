from abc import ABC
from enum import auto
from typing import Dict, List

from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError


class LocalCommInterface(StrEnum):
    """
    Categorization of in-house comm mechanisms for SCADA

    Choices and descriptions:

      * UNKNOWN:
      * I2C:
      * ETHERNET:
      * ONEWIRE:
      * RS485:
      * SIMRABBIT:
      * WIFI:
      * ANALOG_4_20_MA:
      * RS232:
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


class LocalCommInterface100GtEnum(ABC):
    symbols: List[str] = [
        "00000000",
        "653c73b8",
        "0843a726",
        "9ec8bc49",
        "46ac6589",
        "efc144cd",
        "c1e7a955",
        "ae2d4cd8",
        "a6a4ac9f",
        #
    ]


class LocalCommInterfaceGtEnum(LocalCommInterface100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class LocalCommInterfaceMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not LocalCommInterfaceGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {LocalCommInterfaceMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, local_comm_interface):
        if not isinstance(local_comm_interface, LocalCommInterface):
            raise MpSchemaError(
                f"{local_comm_interface} must be of type {LocalCommInterface}"
            )
        return cls.local_to_gt_dict[local_comm_interface]

    gt_to_local_dict: Dict[str, LocalCommInterface] = {
        "00000000": LocalCommInterface.UNKNOWN,
        "653c73b8": LocalCommInterface.ANALOG_4_20_MA,
        "0843a726": LocalCommInterface.RS232,
        "9ec8bc49": LocalCommInterface.I2C,
        "46ac6589": LocalCommInterface.WIFI,
        "efc144cd": LocalCommInterface.SIMRABBIT,
        "c1e7a955": LocalCommInterface.ETHERNET,
        "ae2d4cd8": LocalCommInterface.ONEWIRE,
        "a6a4ac9f": LocalCommInterface.RS485,
    }

    local_to_gt_dict: Dict[LocalCommInterface, str] = {
        LocalCommInterface.UNKNOWN: "00000000",
        LocalCommInterface.I2C: "9ec8bc49",
        LocalCommInterface.ETHERNET: "c1e7a955",
        LocalCommInterface.ONEWIRE: "ae2d4cd8",
        LocalCommInterface.RS485: "a6a4ac9f",
        LocalCommInterface.SIMRABBIT: "efc144cd",
        LocalCommInterface.WIFI: "46ac6589",
        LocalCommInterface.ANALOG_4_20_MA: "653c73b8",
        LocalCommInterface.RS232: "0843a726",
        #
    }
