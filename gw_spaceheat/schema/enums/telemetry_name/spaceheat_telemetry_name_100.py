"""spaceheat.telemetry.name.100 definition"""
from abc import ABC
import enum
from typing import List


class TelemetryName(enum.Enum):
    WATERTEMPFTIMES1000 = "WaterTempFTimes1000"
    WATERFLOWGPMTIMES100 = "WaterFlowGpmTimes100"
    WATERTEMPCTIMES1000 = "WaterTempCTimes1000"
    RELAYSTATE = "RelayState"
    

class SpaceheatTelemetryName100GtEnum(ABC):
    symbols: List[str] = ["793505aa",
                          "d70cce28",
                          "c89d0ba1",
                          "5a71d4b3",
                          ]
