"""Base for gt.sh.simple.status.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status_maker import (
    GtShSimpleSingleStatus,
)


class GtShSimpleStatusBase(NamedTuple):
    AboutGNodeAlias: str  #
    SlotStartUnixS: int  #
    ReportingPeriodS: int  #
    SimpleSingleStatusList: List[GtShSimpleSingleStatus]
    TypeAlias: str = "gt.sh.simple.status.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        simple_single_status_list = []
        for elt in self.SimpleSingleStatusList:
            simple_single_status_list.append(elt.asdict())
        d["SimpleSingleStatusList"] = simple_single_status_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.AboutGNodeAlias, str):
            errors.append(f"AboutGNodeAlias {self.AboutGNodeAlias} must have type str.")
        if not property_format.is_lrd_alias_format(self.AboutGNodeAlias):
            errors.append(
                f"AboutGNodeAlias {self.AboutGNodeAlias}" " must have format LrdAliasFormat"
            )
        if not isinstance(self.SlotStartUnixS, int):
            errors.append(f"SlotStartUnixS {self.SlotStartUnixS} must have type int.")
        if not isinstance(self.ReportingPeriodS, int):
            errors.append(f"ReportingPeriodS {self.ReportingPeriodS} must have type int.")
        if not isinstance(self.SimpleSingleStatusList, list):
            errors.append(
                f"SimpleSingleStatusList {self.SimpleSingleStatusList} must have type list."
            )
        else:
            for elt in self.SimpleSingleStatusList:
                if not isinstance(elt, GtShSimpleSingleStatus):
                    errors.append(
                        f"{elt} of self.SimpleSingleStatusList must have type GtShSimpleSingleStatus."
                    )
        if self.TypeAlias != "gt.sh.simple.status.100":
            errors.append(
                f"Type requires TypeAlias of gt.sh.simple.status.100, not {self.TypeAlias}."
            )

        return errors
