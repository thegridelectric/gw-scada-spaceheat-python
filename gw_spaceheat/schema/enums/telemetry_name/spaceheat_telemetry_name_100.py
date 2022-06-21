"""spaceheat.telemetry.name.100 definition"""
from abc import ABC
import enum
from typing import List


class TelemetryName(enum.Enum):
    
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    WATER_TEMP_F_TIMES1000 = "WaterTempFTimes1000"
    WATER_FLOW_GPM_TIMES100 = "WaterFlowGpmTimes100"
    WATER_TEMP_C_TIMES1000 = "WaterTempCTimes1000"
    RELAY_STATE = "RelayState"
    

class SpaceheatTelemetryName100GtEnum(ABC):
    symbols: List[str] = ["793505aa",
                          "d70cce28",
                          "c89d0ba1",
                          "5a71d4b3",
                          ]
