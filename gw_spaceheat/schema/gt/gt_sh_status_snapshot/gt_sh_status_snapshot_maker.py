"""Makes gt.sh.status.snapshot.110 type"""

import json
from typing import List

from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot import GtShStatusSnapshot
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtShStatusSnapshot_Maker:
    type_alias = 'gt.sh.status.snapshot.110'

    def __init__(self,
                 about_node_alias_list: List[str],
                 report_time_unix_ms: int,
                 value_list: List[int],
                 telemetry_name_list: List[TelemetryName]):

        tuple = GtShStatusSnapshot(TelemetryNameList=telemetry_name_list,
                                   AboutNodeAliasList=about_node_alias_list,
                                   ReportTimeUnixMs=report_time_unix_ms,
                                   ValueList=value_list,
                                   )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShStatusSnapshot) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShStatusSnapshot:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShStatusSnapshot:
        if "AboutNodeAliasList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing AboutNodeAliasList")
        if "ReportTimeUnixMs" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ReportTimeUnixMs")
        if "ValueList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ValueList")
        if "TelemetryNameList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TelemetryNameList")
        else:
            telemetry_name_list = []
            for elt in d["TelemetryNameList"]:
                telemetry_name_list.append(TelemetryNameMap.gt_to_local(elt))
            d["TelemetryNameList"] = telemetry_name_list

        tuple = GtShStatusSnapshot(TelemetryNameList=d["TelemetryNameList"],
                                   AboutNodeAliasList=d["AboutNodeAliasList"],
                                   ReportTimeUnixMs=d["ReportTimeUnixMs"],
                                   ValueList=d["ValueList"],
                                   )
        tuple.check_for_errors()
        return tuple
