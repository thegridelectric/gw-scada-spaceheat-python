"""Makes gt.sh.multipurpose.telemetry.status.100 type"""
import json
from typing import List

from schema.gt.gt_sh_multipurpose_telemetry_status.gt_sh_multipurpose_telemetry_status import GtShMultipurposeTelemetryStatus
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtShMultipurposeTelemetryStatus_Maker:
    type_alias = "gt.sh.multipurpose.telemetry.status.100"

    def __init__(self,
                 about_node_alias: str,
                 telemetry_name: TelemetryName,
                 value_list: List[int],
                 read_time_unix_ms_list: List[int],
                 sensor_node_alias: str):

        gw_tuple = GtShMultipurposeTelemetryStatus(
            AboutNodeAlias=about_node_alias,
            TelemetryName=telemetry_name,
            ValueList=value_list,
            ReadTimeUnixMsList=read_time_unix_ms_list,
            SensorNodeAlias=sensor_node_alias,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShMultipurposeTelemetryStatus) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShMultipurposeTelemetryStatus:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShMultipurposeTelemetryStatus:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "AboutNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeAlias")
        if "TelemetryNameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameGtEnumSymbol")
        new_d["TelemetryName"] = TelemetryNameMap.gt_to_local(new_d["TelemetryNameGtEnumSymbol"])
        if "ValueList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ValueList")
        if "ReadTimeUnixMsList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReadTimeUnixMsList")
        if "SensorNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SensorNodeAlias")

        gw_tuple = GtShMultipurposeTelemetryStatus(
            TypeAlias=new_d["TypeAlias"],
            AboutNodeAlias=new_d["AboutNodeAlias"],
            TelemetryName=new_d["TelemetryName"],
            ValueList=new_d["ValueList"],
            ReadTimeUnixMsList=new_d["ReadTimeUnixMsList"],
            SensorNodeAlias=new_d["SensorNodeAlias"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
