"""Makes gt.spaceheat.async.single.100 type"""

import json
from typing import List


from schema.gt.gt_spaceheat_async_single.gt_spaceheat_async_single import GtSpaceheatAsyncSingle
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtSpaceheatAsyncSingle_Maker():
    type_alias = 'gt.spaceheat.async.single.100'

    def __init__(self,
                 value_list: List[int],
                 sh_node_alias: str,
                 unix_time_s_list: List[int],
                 telemetry_name: TelemetryName):

        tuple = GtSpaceheatAsyncSingle(ValueList=value_list,
                                       ShNodeAlias=sh_node_alias,
                                       UnixTimeSList=unix_time_s_list,
                                       TelemetryName=telemetry_name,
                                       )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtSpaceheatAsyncSingle) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtSpaceheatAsyncSingle:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtSpaceheatAsyncSingle:
        if "ValueList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ValueList")
        if "ShNodeAlias" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ShNodeAlias")
        if "UnixTimeSList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing UnixTimeSList")
        if "TelemetryNameGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TelemetryNameGtEnumSymbol")
        d["TelemetryName"] = TelemetryNameMap.gt_to_local(d["TelemetryNameGtEnumSymbol"])

        tuple = GtSpaceheatAsyncSingle(ValueList=d["ValueList"],
                                       ShNodeAlias=d["ShNodeAlias"],
                                       UnixTimeSList=d["UnixTimeSList"],
                                       TelemetryName=d["TelemetryName"],
                                       )
        tuple.check_for_errors()
        return tuple
