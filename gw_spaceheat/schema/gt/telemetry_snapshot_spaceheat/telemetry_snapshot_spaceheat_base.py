"""Base for telemetry.snapshot.spaceheat.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.enums import (
    TelemetryName,
    TelemetryNameMap,
)


class TelemetrySnapshotSpaceheatBase(NamedTuple):
    AboutNodeAliasList: List[str]
    ValueList: List[int]
    TelemetryNameList: List[TelemetryName]
    ReportTimeUnixMs: int  #
    TypeAlias: str = "telemetry.snapshot.spaceheat.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.TelemetryNameList:
            telemetry_name_list.append(TelemetryNameMap.local_to_gt(elt))
        d["TelemetryNameList"] = telemetry_name_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.AboutNodeAliasList, list):
            errors.append(
                f"AboutNodeAliasList {self.AboutNodeAliasList} must have type list."
            )
        else:
            for elt in self.AboutNodeAliasList:
                if not isinstance(elt, str):
                    errors.append(
                        f"elt {elt} of AboutNodeAliasList must have type str."
                    )
                if not property_format.is_lrd_alias_format(elt):
                    errors.append(
                        f"elt {elt} of AboutNodeAliasList must have format LrdAliasFormat"
                    )
        if not isinstance(self.ValueList, list):
            errors.append(
                f"ValueList {self.ValueList} must have type list."
            )
        else:
            for elt in self.ValueList:
                if not isinstance(elt, int):
                    errors.append(
                        f"elt {elt} of ValueList must have type int."
                    )
        if not isinstance(self.TelemetryNameList, list):
            errors.append(
                f"TelemetryNameList {self.TelemetryNameList} must have type list."
            )
        else:
            for elt in self.TelemetryNameList:
                if not isinstance(elt, TelemetryName):
                    errors.append(
                        f"elt {elt} of TelemetryNameList must have type TelemetryName."
                    )
        if not isinstance(self.ReportTimeUnixMs, int):
            errors.append(
                f"ReportTimeUnixMs {self.ReportTimeUnixMs} must have type int."
            )
        if not property_format.is_reasonable_unix_time_ms(self.ReportTimeUnixMs):
            errors.append(
                f"ReportTimeUnixMs {self.ReportTimeUnixMs}"
                " must have format ReasonableUnixTimeMs"
            )
        if self.TypeAlias != "telemetry.snapshot.spaceheat.100":
            errors.append(
                f"Type requires TypeAlias of telemetry.snapshot.spaceheat.100, not {self.TypeAlias}."
            )

        return errors
