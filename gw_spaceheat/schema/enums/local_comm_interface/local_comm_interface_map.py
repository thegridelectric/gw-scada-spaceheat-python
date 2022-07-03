from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.local_comm_interface.local_comm_interface_100 import (
    LocalCommInterface,
    LocalCommInterface100GtEnum,
)


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
            raise MpSchemaError(f"{local_comm_interface} must be of type {LocalCommInterface}")
        return cls.local_to_gt_dict[local_comm_interface]

    gt_to_local_dict: Dict[str, LocalCommInterface] = {
        "653c73b8": LocalCommInterface.ANALOG_4_20_MA,
        "0843a726": LocalCommInterface.RS232,
        "9ec8bc49": LocalCommInterface.I2C,
        "46ac6589": LocalCommInterface.WIFI,
        "efc144cd": LocalCommInterface.SIMRABBIT,
        "829549d1": LocalCommInterface.UNKNOWN,
        "c1e7a955": LocalCommInterface.ETHERNET,
        "ae2d4cd8": LocalCommInterface.ONEWIRE,
        "a6a4ac9f": LocalCommInterface.RS485,
    }

    local_to_gt_dict: Dict[LocalCommInterface, str] = {
        LocalCommInterface.ANALOG_4_20_MA: "653c73b8",
        LocalCommInterface.RS232: "0843a726",
        LocalCommInterface.I2C: "9ec8bc49",
        LocalCommInterface.WIFI: "46ac6589",
        LocalCommInterface.SIMRABBIT: "efc144cd",
        LocalCommInterface.UNKNOWN: "829549d1",
        LocalCommInterface.ETHERNET: "c1e7a955",
        LocalCommInterface.ONEWIRE: "ae2d4cd8",
        LocalCommInterface.RS485: "a6a4ac9f",
        #
    }
