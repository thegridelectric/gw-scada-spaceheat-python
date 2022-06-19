"""Makes gt.sh.simple.single.status.100 type"""

import json
from typing import List

from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status \
    import GtShSimpleSingleStatus
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtShSimpleSingleStatus_Maker():
    type_alias = 'gt.sh.simple.single.status.100'

    def __init__(self,
                 read_time_unix_ms_list: List[int],
                 sh_node_alias: str,
                 value_list: List[int],
                 telemetry_name: TelemetryName):

        tuple = GtShSimpleSingleStatus(ReadTimeUnixMsList=read_time_unix_ms_list,
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
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShSimpleSingleStatus:
        if "ReadTimeUnixMsList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ReadTimeUnixMsList")
        if "ShNodeAlias" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ShNodeAlias")
        if "ValueList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ValueList")
        if "TelemetryNameGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TelemetryNameGtEnumSymbol")
        d["TelemetryName"] = TelemetryNameMap.gt_to_local(d["TelemetryNameGtEnumSymbol"])

        tuple = GtShSimpleSingleStatus(ReadTimeUnixMsList=d["ReadTimeUnixMsList"],
                                       TelemetryName=d["TelemetryName"],
                                       ShNodeAlias=d["ShNodeAlias"],
                                       ValueList=d["ValueList"],
                                       )
        tuple.check_for_errors()
        return tuple
