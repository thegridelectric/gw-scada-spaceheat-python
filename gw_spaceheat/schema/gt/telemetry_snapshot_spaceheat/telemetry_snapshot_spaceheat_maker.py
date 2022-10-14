"""Makes telemetry.snapshot.spaceheat.100 type"""
import json
from typing import List

from schema.gt.telemetry_snapshot_spaceheat.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat
from schema.errors import MpSchemaError
from schema.enums import (
    TelemetryName,
    TelemetryNameMap,
)


class TelemetrySnapshotSpaceheat_Maker:
    type_alias = "telemetry.snapshot.spaceheat.100"

    def __init__(self,
                 about_node_alias_list: List[str],
                 value_list: List[int],
                 telemetry_name_list: List[TelemetryName],
                 report_time_unix_ms: int):

        gw_tuple = TelemetrySnapshotSpaceheat(
            AboutNodeAliasList=about_node_alias_list,
            ValueList=value_list,
            TelemetryNameList=telemetry_name_list,
            ReportTimeUnixMs=report_time_unix_ms,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: TelemetrySnapshotSpaceheat) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> TelemetrySnapshotSpaceheat:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> TelemetrySnapshotSpaceheat:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "AboutNodeAliasList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeAliasList")
        if "ValueList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ValueList")
        if "TelemetryNameList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameList")
        telemetry_name_list = []
        for elt in new_d["TelemetryNameList"]:
            telemetry_name_list.append(TelemetryNameMap.gt_to_local(elt))
        new_d["TelemetryNameList"] = telemetry_name_list
        if "ReportTimeUnixMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReportTimeUnixMs")

        gw_tuple = TelemetrySnapshotSpaceheat(
            TypeAlias=new_d["TypeAlias"],
            AboutNodeAliasList=new_d["AboutNodeAliasList"],
            ValueList=new_d["ValueList"],
            TelemetryNameList=new_d["TelemetryNameList"],
            ReportTimeUnixMs=new_d["ReportTimeUnixMs"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
