"""local.comm.interface.100 definition"""
import enum
from abc import ABC
from typing import List


class LocalCommInterface(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    ANALOG_4_20_MA = "Analog_4_20_mA"
    RS232 = "RS232"
    I2C = "I2C"
    WIFI = "Wifi"
    SIMRABBIT = "SimRabbit"
    UNKNOWN = "Unknown"
    ETHERNET = "Ethernet"
    ONEWIRE = "OneWire"
    RS485 = "RS485"
    #


class LocalCommInterface100GtEnum(ABC):
    symbols: List[str] = [
        "653c73b8",
        "0843a726",
        "9ec8bc49",
        "46ac6589",
        "efc144cd",
        "829549d1",
        "c1e7a955",
        "ae2d4cd8",
        "a6a4ac9f",
        #
    ]
