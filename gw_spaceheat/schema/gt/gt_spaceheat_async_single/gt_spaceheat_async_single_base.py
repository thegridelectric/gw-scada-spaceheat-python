"""Base for gt.spaceheat.async.single.100"""
import json
from typing import List, NamedTuple
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtSpaceheatAsyncSingleBase(NamedTuple):
    ValueList: List[int]   #
    ShNodeAlias: str     #
    UnixTimeSList: List[int]     #
    TelemetryName: TelemetryName     #
    TypeAlias: str = 'gt.spaceheat.async.single.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del(d["TelemetryName"])
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ValueList, list):
            errors.append(f"ValueList {self.ValueList} must have type list.")
        else:
            for elt in self.ValueList:
                if not isinstance(elt, int):
                    errors.append(f"{elt} of self.UnixTimeSList must have type int.")
        if not isinstance(self.ShNodeAlias, str):
            errors.append(f"ShNodeAlias {self.ShNodeAlias} must have type str.")
        if not isinstance(self.UnixTimeSList, list):
            errors.append(f"UnixTimeSList {self.UnixTimeSList} must have type list.")
        else:
            for elt in self.UnixTimeSList:
                if not isinstance(elt, int):
                    errors.append(f"{elt} of self.UnixTimeSList must have type int.")
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(f"TelemetryName {self.TelemetryName} must have type {TelemetryName}.")
        if self.TypeAlias != 'gt.spaceheat.async.single.100':
            errors.append(f"Type requires TypeAlias of gt.spaceheat.async.single.100, not {self.TypeAlias}.")
        
        return errors
