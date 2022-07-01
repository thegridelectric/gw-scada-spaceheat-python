"""Makes gt.sh.telemetry.from.multipurpose.sensor.100 type"""
import json
from typing import List

from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor import GtShTelemetryFromMultipurposeSensor
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtShTelemetryFromMultipurposeSensor_Maker:
    type_alias = "gt.sh.telemetry.from.multipurpose.sensor.100"

    def __init__(self,
                 about_node_alias_list: List[str],
                 value_list: List[int],
                 scada_read_time_unix_ms: int,
                 telemetry_name_list: List[TelemetryName]):

        gw_tuple = GtShTelemetryFromMultipurposeSensor(
            AboutNodeAliasList=about_node_alias_list,
            ValueList=value_list,
            ScadaReadTimeUnixMs=scada_read_time_unix_ms,
            TelemetryNameList=telemetry_name_list,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShTelemetryFromMultipurposeSensor) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShTelemetryFromMultipurposeSensor:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShTelemetryFromMultipurposeSensor:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "AboutNodeAliasList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeAliasList")
        if "ValueList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ValueList")
        if "ScadaReadTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ScadaReadTimeUnixMs")
        if "TelemetryNameList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameList")
        telemetry_name_list = []
        for elt in new_d["TelemetryNameList"]:
            telemetry_name_list.append(TelemetryNameMap.gt_to_local(elt))
        new_d["TelemetryNameList"] = telemetry_name_list

        gw_tuple = GtShTelemetryFromMultipurposeSensor(
            TypeAlias=new_d["TypeAlias"],
            AboutNodeAliasList=new_d["AboutNodeAliasList"],
            ValueList=new_d["ValueList"],
            ScadaReadTimeUnixMs=new_d["ScadaReadTimeUnixMs"],
            TelemetryNameList=new_d["TelemetryNameList"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
