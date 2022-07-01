"""Makes gt.telemetry.110 type"""
import json

from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtTelemetry_Maker:
    type_alias = "gt.telemetry.110"

    def __init__(self,
                 scada_read_time_unix_ms: int,
                 value: int,
                 name: TelemetryName,
                 exponent: int):

        gw_tuple = GtTelemetry(
            ScadaReadTimeUnixMs=scada_read_time_unix_ms,
            Value=value,
            Name=name,
            Exponent=exponent,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtTelemetry) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtTelemetry:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtTelemetry:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ScadaReadTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ScadaReadTimeUnixMs")
        if "Value" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Value")
        if "NameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing NameGtEnumSymbol")
        new_d["Name"] = TelemetryNameMap.gt_to_local(new_d["NameGtEnumSymbol"])
        if "Exponent" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Exponent")

        gw_tuple = GtTelemetry(
            TypeAlias=new_d["TypeAlias"],
            ScadaReadTimeUnixMs=new_d["ScadaReadTimeUnixMs"],
            Value=new_d["Value"],
            Name=new_d["Name"],
            Exponent=new_d["Exponent"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
