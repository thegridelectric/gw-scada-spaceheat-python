"""Base for gt.spaceheat.sync.single.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtSpaceheatSyncSingleBase(NamedTuple):
    FirstReadTimeUnixS: int
    SamplePeriodS: int     #
    ShNodeAlias: str     #
    ValueList: List[int]    #
    TelemetryName: TelemetryName     #
    TypeAlias: str = 'gt.spaceheat.sync.single.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del(d["TelemetryName"])
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.FirstReadTimeUnixS, int):
            errors.append(f"FirstReadTimeUnixS {self.FirstReadTimeUnixS} must have type int.")
        if not isinstance(self.SamplePeriodS, int):
            errors.append(f"SamplePeriodS {self.SamplePeriodS} must have type int.")
        if not isinstance(self.ShNodeAlias, str):
            errors.append(f"ShNodeAlias {self.ShNodeAlias} must have type str.")
        if not property_format.is_lrd_alias_format(self.ShNodeAlias):
            errors.append(f"ShNodeAlias {self.ShNodeAlias}"
                          " must have format LrdAliasFormat")
        if not isinstance(self.ValueList, list):
            errors.append(f"ValueList {self.ValueList} must have type list.")
        for elt in self.ValueList:
            if not isinstance(elt, int):
                errors.append(f"elt {elt} of ValueList must have type int")
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(f"TelemetryName {self.TelemetryName} must have type {TelemetryName}.")
        if self.TypeAlias != 'gt.spaceheat.sync.single.100':
            errors.append(f"Type requires TypeAlias of gt.spaceheat.sync.single.100, not {self.TypeAlias}.")
        
        return errors
