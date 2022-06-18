"""Base for gt.sh.simple.single.status.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtShSimpleSingleStatusBase(NamedTuple):
    ReadTimeUnixMsList: List[int]
    ShNodeAlias: str     #
    ValueList: List[int]    #
    TelemetryName: TelemetryName     #
    TypeAlias: str = 'gt.sh.simple.single.status.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del(d["TelemetryName"])
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ReadTimeUnixMsList, list):
            errors.append(f"ReadTimeUnixMsList {self.ReadTimeUnixMsList} must have type list.")
        else:
            for elt in self.ReadTimeUnixMsList:
                if not isinstance(elt, int):
                    errors.append(f"elt {elt} of ReadTimeUnixMsList must have type int")
                if not property_format.is_reasonable_unix_time_ms(elt):
                    errors.append(f"elt {elt} of ReadTimeUnixMsList must reasonble_unix_time_ms format")
        if not isinstance(self.ShNodeAlias, str):
            errors.append(f"ShNodeAlias {self.ShNodeAlias} must have type str.")
        if not property_format.is_lrd_alias_format(self.ShNodeAlias):
            errors.append(f"ShNodeAlias {self.ShNodeAlias}"
                          " must have format LrdAliasFormat")
        if not isinstance(self.ValueList, list):
            errors.append(f"ValueList {self.ValueList} must have type list.")
        else:
            for elt in self.ValueList:
                if not isinstance(elt, int):
                    errors.append(f"elt {elt} of ValueList must have type int")
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(f"TelemetryName {self.TelemetryName} must have type {TelemetryName}.")
        if self.TypeAlias != 'gt.sh.simple.single.status.100':
            errors.append(f"Type requires TypeAlias of gt.sh.simple.single.status.100, not {self.TypeAlias}.")
        
        return errors
