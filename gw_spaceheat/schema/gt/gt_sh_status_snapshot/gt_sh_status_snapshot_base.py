"""Base for gt.sh.status.snapshot"""
import json
from typing import List, Optional, NamedTuple
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtShStatusSnapshotBase(NamedTuple):
    ReportTimeUnixS: int     #
    AboutNodeList: List[str]
    ValueList: List[int]
    TelemetryNameList: List[TelemetryName]    #
    TypeAlias: str = 'gt.sh.status.snapshot.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del(d["TelemetryNameList"])
        telemetry_name_list = []
        for elt in self.TelemetryNameList:
            telemetry_name_list.append(TelemetryNameMap.local_to_gt(elt))
        d["TelemetryNameList"] = telemetry_name_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.AboutNodeList, list):
            errors.append(f"AboutNodeList {self.AboutNodeList} must have type list.")
        else:
            for elt in self.AboutNodeList:
                if not isinstance(elt, str):
                    errors.append(f"elt {elt} of AboutNodeAlias must have type str!")
                if not property_format.is_lrd_alias_format(elt):
                    errors.append(f"elt {elt} of AboutNodeList "
                                " must have format LrdAliasFormat")
        if not isinstance(self.ReportTimeUnixS, int):
            errors.append(f"ReportTimeUnixS {self.ReportTimeUnixS} must have type int.")
        if not property_format.is_reasonable_unix_time_s(self.ReportTimeUnixS):
            errors.append(f"ReportTimeUnixS {self.ReportTimeUnixS}"
                          " must have format ReasonableUnixTimeS")
        if not isinstance(self.ValueList, list):
            errors.append(f"ValueList {self.ValueList} must have type list.")
        else:
            for elt in self.ValueList:
                if not isinstance(elt, int):
                    errors.append(f"elt {elt} of ValueList must have type int.")
        if not isinstance(self.TelemetryNameList, list):
            errors.append(f"TelemetryNameList {self.TelemetryNameList} must have type list.")
        else:
            for elt in self.TelemetryNameList:
                if not isinstance(elt, TelemetryName):
                    errors.append(f"elt {elt} of TelemetryNameList must have type TelemetryName!")
        if self.TypeAlias != 'gt.sh.status.snapshot.100':
            errors.append(f"Type requires TypeAlias of gt.sh.status.snapshot.100, not {self.TypeAlias}.")
    
        return errors
