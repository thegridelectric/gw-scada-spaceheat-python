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
        "00000000": TelemetryName.UNKNOWN,
        "af39eec9": TelemetryName.POWER_W,
        "5a71d4b3": TelemetryName.RELAY_STATE,
        "c89d0ba1": TelemetryName.WATER_TEMP_C_TIMES1000,
        "793505aa": TelemetryName.WATER_TEMP_F_TIMES1000,
        "d70cce28": TelemetryName.GPM_TIMES100,
        "ad19e79c": TelemetryName.CURRENT_RMS_MICRO_AMPS,
        "329a68c0": TelemetryName.GALLONS_TIMES100,
        "bb6fdd59": TelemetryName.VOLTAGE_RMS_MILLI_AMPS,
        "e0bb014b": TelemetryName.MILLI_WATT_HOURS,
        "337b8659": TelemetryName.FREQUENCY_MICRO_HZ,
        "0f627faa": TelemetryName.AIR_TEMP_C_TIMES1000,
        "4c3f8c78": TelemetryName.AIR_TEMP_F_TIMES1000,
    }

    local_to_gt_dict: Dict[TelemetryName, str] = {
        TelemetryName.UNKNOWN: "00000000",
        TelemetryName.POWER_W: "af39eec9",
        TelemetryName.RELAY_STATE: "5a71d4b3",
        TelemetryName.WATER_TEMP_C_TIMES1000: "c89d0ba1",
        TelemetryName.WATER_TEMP_F_TIMES1000: "793505aa",
        TelemetryName.GPM_TIMES100: "d70cce28",
        TelemetryName.CURRENT_RMS_MICRO_AMPS: "ad19e79c",
        TelemetryName.GALLONS_TIMES100: "329a68c0",
        TelemetryName.VOLTAGE_RMS_MILLI_AMPS: "bb6fdd59",
        TelemetryName.MILLI_WATT_HOURS: "e0bb014b",
        TelemetryName.FREQUENCY_MICRO_HZ: "337b8659",
        TelemetryName.AIR_TEMP_C_TIMES1000: "0f627faa",
        TelemetryName.AIR_TEMP_F_TIMES1000: "4c3f8c78",
    }

