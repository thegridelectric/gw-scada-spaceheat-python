"""Makes gt.sh.simple.single.status.100 type"""

import json
from typing import List

from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status import GtShSimpleSingleStatus
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtShSimpleSingleStatus_Maker:
    type_alias = "gt.sh.simple.single.status.100"

    def __init__(
        self,
        read_time_unix_ms_list: List[int],
        sh_node_alias: str,
        value_list: List[int],
        telemetry_name: TelemetryName,
    ):

        tuple = GtShSimpleSingleStatus(
            ReadTimeUnixMsList=read_time_unix_ms_list,
            TelemetryName=telemetry_name,
            ShNodeAlias=sh_node_alias,
            ValueList=value_list,
        )
        tuple.check_for_errors()
        self.tuple: GtShSimpleSingleStatus = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShSimpleSingleStatus) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShSimpleSingleStatus:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShSimpleSingleStatus:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]

        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ReadTimeUnixMsList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReadTimeUnixMsList")
        if "ShNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeAlias")
        if "ValueList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ValueList")
        if "TelemetryNameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameGtEnumSymbol")
        new_d["TelemetryName"] = TelemetryNameMap.gt_to_local(new_d["TelemetryNameGtEnumSymbol"])

        tuple = GtShSimpleSingleStatus(
            TypeAlias=new_d["TypeAlias"],
            ReadTimeUnixMsList=new_d["ReadTimeUnixMsList"],
            TelemetryName=new_d["TelemetryName"],
            ShNodeAlias=new_d["ShNodeAlias"],
            ValueList=new_d["ValueList"],
        )
        tuple.check_for_errors()
        return tuple
