"""spaceheat.telemetry.name.100 definition"""
import enum
from abc import ABC
from typing import List


class TelemetryName(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    UNKNOWN = "Unknown"
    POWER_W = "PowerW"
    RELAY_STATE = "RelayState"
    WATER_TEMP_C_TIMES1000 = "WaterTempCTimes1000"
    WATER_TEMP_F_TIMES1000 = "WaterTempFTimes1000"
    GPM_TIMES100 = "GpmTimes100"
    CURRENT_RMS_MICRO_AMPS = "CurrentRmsMicroAmps"
    GALLONS_TIMES100 = "GallonsTimes100"
    VOLTAGE_RMS_MILLI_AMPS = "VoltageRmsMilliAmps"
    MILLI_WATT_HOURS = "MilliWattHours"
    FREQUENCY_MICRO_HZ = "FrequencyMicroHz"
    AIR_TEMP_C_TIMES1000 = "AirTempCTimes1000"
    AIR_TEMP_F_TIMES1000 = "AirTempFTimes1000"


class SpaceheatTelemetryName100GtEnum(ABC):
    symbols: List[str] = [
        "00000000",
        "af39eec9",
        "5a71d4b3",
        "c89d0ba1",
        "793505aa",
        "d70cce28",
        "ad19e79c",
        "329a68c0",
        "bb6fdd59",
        "e0bb014b",
        "337b8659",
        "0f627faa",
        "4c3f8c78",
    ]
