"""Makes gt.sh.telemetry.from.multipurpose.sensor.100 type"""

import json
from typing import List

from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor \
    import GtShTelemetryFromMultipurposeSensor
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtShTelemetryFromMultipurposeSensor_Maker():
    type_alias = 'gt.sh.telemetry.from.multipurpose.sensor.100'

    def __init__(self,
                 about_node_alias_list: List[str],
                 scada_read_time_unix_ms: int,
                 value_list: List[int],
                 telemetry_name_list: List[TelemetryName]):

        tuple = GtShTelemetryFromMultipurposeSensor(TelemetryNameList=telemetry_name_list,
                                                    AboutNodeAliasList=about_node_alias_list,
                                                    ScadaReadTimeUnixMs=scada_read_time_unix_ms,
                                                    ValueList=value_list,
                                                    )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShTelemetryFromMultipurposeSensor) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShTelemetryFromMultipurposeSensor:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShTelemetryFromMultipurposeSensor:
        if "AboutNodeAliasList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing AboutNodeAliasList")
        if "ScadaReadTimeUnixMs" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ScadaReadTimeUnixMs")
        if "ValueList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ValueList")
        if "TelemetryNameList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TelemetryNameList")
        else:
            telemetry_name_list = []
            for elt in d["TelemetryNameList"]:
                telemetry_name_list.append(TelemetryNameMap.gt_to_local(elt))
            d["TelemetryNameList"] = telemetry_name_list

        tuple = GtShTelemetryFromMultipurposeSensor(TelemetryNameList=d["TelemetryNameList"],
                                                    AboutNodeAliasList=d["AboutNodeAliasList"],
                                                    ScadaReadTimeUnixMs=d["ScadaReadTimeUnixMs"],
                                                    ValueList=d["ValueList"],
                                                    )
        tuple.check_for_errors()
        return tuple
