"""Makes gt.telemetry type"""

import json
from typing import Dict, Optional


from schema.gt.gt_telemetry.gt_telemetry import GtTelemetry
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtTelemetry_Maker():
    type_alias = 'gt.telemetry.110'

    def __init__(self,
                    scada_read_time_unix_ms: int,
                    value: int,
                    exponent: int,
                    name: TelemetryName):

        tuple = GtTelemetry(ScadaReadTimeUnixMs=scada_read_time_unix_ms,
                                            Value=value,
                                            Name=name,
                                            Exponent=exponent,
                                            )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtTelemetry) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtTelemetry:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtTelemetry:
        if "ScadaReadTimeUnixMs" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ScadaReadTimeUnixMs")
        if "Value" not in d.keys():
            raise MpSchemaError(f"dict {d} missing Value")
        if "Exponent" not in d.keys():
            raise MpSchemaError(f"dict {d} missing Exponent")
        if "SpaceheatTelemetryNameGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SpaceheatTelemetryNameGtEnumSymbol")
        d["Name"] = TelemetryNameMap.gt_to_local(d["SpaceheatTelemetryNameGtEnumSymbol"])

        tuple = GtTelemetry(ScadaReadTimeUnixMs=d["ScadaReadTimeUnixMs"],
                                            Value=d["Value"],
                                            Name=d["Name"],
                                            Exponent=d["Exponent"],
                                            )
        tuple.check_for_errors()
        return tuple
