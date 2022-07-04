"""Makes gt.sh.simple.telemetry.status.100 type"""
import json
from typing import List

from schema.gt.gt_sh_simple_telemetry_status.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtShSimpleTelemetryStatus_Maker:
    type_alias = "gt.sh.simple.telemetry.status.100"

    def __init__(self,
                 value_list: List[int],
                 read_time_unix_ms_list: List[int],
                 telemetry_name: TelemetryName,
                 sh_node_alias: str):

        gw_tuple = GtShSimpleTelemetryStatus(
            ValueList=value_list,
            ReadTimeUnixMsList=read_time_unix_ms_list,
            TelemetryName=telemetry_name,
            ShNodeAlias=sh_node_alias,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShSimpleTelemetryStatus) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShSimpleTelemetryStatus:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShSimpleTelemetryStatus:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ValueList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ValueList")
        if "ReadTimeUnixMsList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReadTimeUnixMsList")
        if "TelemetryNameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameGtEnumSymbol")
        new_d["TelemetryName"] = TelemetryNameMap.gt_to_local(new_d["TelemetryNameGtEnumSymbol"])
        if "ShNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeAlias")

        gw_tuple = GtShSimpleTelemetryStatus(
            TypeAlias=new_d["TypeAlias"],
            ValueList=new_d["ValueList"],
            ReadTimeUnixMsList=new_d["ReadTimeUnixMsList"],
            TelemetryName=new_d["TelemetryName"],
            ShNodeAlias=new_d["ShNodeAlias"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
