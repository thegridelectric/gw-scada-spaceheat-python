from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import (
    TelemetryName,
    SpaceheatTelemetryName100GtEnum,
)


class TelemetryNameGtEnum(SpaceheatTelemetryName100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class TelemetryNameMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not TelemetryNameGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {TelemetryNameMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, telemetry_name):
        if not isinstance(telemetry_name, TelemetryName):
            raise MpSchemaError(f"{telemetry_name} must be of type {TelemetryName}")
        return cls.local_to_gt_dict[telemetry_name]

    gt_to_local_dict: Dict[str, TelemetryName] = {
        "af39eec9": TelemetryName.POWER_W,
        "793505aa": TelemetryName.WATER_TEMP_F_TIMES1000,
        "329a68c0": TelemetryName.GALLONS_PER_MINUTE_TIMES10,
        "d70cce28": TelemetryName.WATER_FLOW_GPM_TIMES100,
        "c89d0ba1": TelemetryName.WATER_TEMP_C_TIMES1000,
        "5a71d4b3": TelemetryName.RELAY_STATE,
        "ad19e79c": TelemetryName.CURRENT_RMS_MICRO_AMPS,
    }

    local_to_gt_dict: Dict[TelemetryName, str] = {
        TelemetryName.POWER_W: "af39eec9",
        TelemetryName.WATER_TEMP_F_TIMES1000: "793505aa",
        TelemetryName.GALLONS_PER_MINUTE_TIMES10: "329a68c0",
        TelemetryName.WATER_FLOW_GPM_TIMES100: "d70cce28",
        TelemetryName.WATER_TEMP_C_TIMES1000: "c89d0ba1",
        TelemetryName.RELAY_STATE: "5a71d4b3",
        TelemetryName.CURRENT_RMS_MICRO_AMPS: "ad19e79c",
        #
    }
