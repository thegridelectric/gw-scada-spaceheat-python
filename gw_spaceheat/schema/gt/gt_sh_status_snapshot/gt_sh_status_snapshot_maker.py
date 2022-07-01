"""Makes gt.sh.status.snapshot.110 type"""
import json
from typing import List

from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot import GtShStatusSnapshot
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtShStatusSnapshot_Maker:
    type_alias = "gt.sh.status.snapshot.110"

    def __init__(self,
                 telemetry_name_list: List[TelemetryName],
                 about_node_alias_list: List[str],
                 report_time_unix_ms: int,
                 value_list: List[int]):

        gw_tuple = GtShStatusSnapshot(
            TelemetryNameList=telemetry_name_list,
            AboutNodeAliasList=about_node_alias_list,
            ReportTimeUnixMs=report_time_unix_ms,
            ValueList=value_list,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShStatusSnapshot) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShStatusSnapshot:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShStatusSnapshot:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "TelemetryNameList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameList")
        telemetry_name_list = []
        for elt in new_d["TelemetryNameList"]:
            telemetry_name_list.append(TelemetryNameMap.gt_to_local(elt))
        new_d["TelemetryNameList"] = telemetry_name_list
        if "AboutNodeAliasList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeAliasList")
        if "ReportTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReportTimeUnixMs")
        if "ValueList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ValueList")

        gw_tuple = GtShStatusSnapshot(
            TypeAlias=new_d["TypeAlias"],
            TelemetryNameList=new_d["TelemetryNameList"],
            AboutNodeAliasList=new_d["AboutNodeAliasList"],
            ReportTimeUnixMs=new_d["ReportTimeUnixMs"],
            ValueList=new_d["ValueList"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
