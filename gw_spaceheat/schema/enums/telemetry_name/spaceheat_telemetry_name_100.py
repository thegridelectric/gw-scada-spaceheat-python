"""spaceheat.telemetry.name.100 definition"""
import enum
from abc import ABC
from typing import List


class TelemetryName(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    POWER_W = "PowerW"
    WATER_TEMP_F_TIMES1000 = "WaterTempFTimes1000"
    GALLONS_PER_MINUTE_TIMES10 = "GallonsPerMinuteTimes10"
    WATER_FLOW_GPM_TIMES100 = "WaterFlowGpmTimes100"
    WATER_TEMP_C_TIMES1000 = "WaterTempCTimes1000"
    RELAY_STATE = "RelayState"
    CURRENT_RMS_MICRO_AMPS = "CurrentRmsMicroAmps"
    #


class SpaceheatTelemetryName100GtEnum(ABC):
    symbols: List[str] = [
        "af39eec9",
        "793505aa",
        "329a68c0",
        "d70cce28",
        "c89d0ba1",
        "5a71d4b3",
        "ad19e79c",
        #
    ]
