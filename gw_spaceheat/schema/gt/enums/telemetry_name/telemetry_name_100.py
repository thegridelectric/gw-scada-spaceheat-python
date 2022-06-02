
   
""" telemetry.name.100 Definition"""
import enum
from typing import Dict, List


class TelemetryName(enum.Enum):
    WATER_FLOW_GPM_TIMES_100 = "WaterFlowGpmTimes100"
    WATER_TEMP_F_TIMES_1000 = "WaterTempFTimes1000"
    WATER_TEMP_C_TIMES_1000 = "WaterTempCTimes1000"


class TelemetryName100GtEnum():
    symbols: List[str] = ["d70cce28-6b3d-47eb-8cc8-fd48204be1de",
                          "793505aa-9cf0-405c-bf46-712babbe55b2",
                          "c89d0ba1-9b77-4d6a-80ad-926d2ef0026b"]

    gt_to_local: Dict[str, TelemetryName] = {
        "d70cce28-6b3d-47eb-8cc8-fd48204be1de": TelemetryName.WATER_FLOW_GPM_TIMES_100,
        "793505aa-9cf0-405c-bf46-712babbe55b2": TelemetryName.WATER_TEMP_F_TIMES_1000,
        "c89d0ba1-9b77-4d6a-80ad-926d2ef0026b": TelemetryName.WATER_TEMP_C_TIMES_1000 
    }

    local_to_gt: Dict[TelemetryName, str] = {
        TelemetryName.WATER_FLOW_GPM_TIMES_100: "d70cce28-6b3d-47eb-8cc8-fd48204be1de",
        TelemetryName.WATER_TEMP_F_TIMES_1000: "793505aa-9cf0-405c-bf46-712babbe55b2",
        TelemetryName.WATER_TEMP_C_TIMES_1000: "c89d0ba1-9b77-4d6a-80ad-926d2ef0026b"
    }

