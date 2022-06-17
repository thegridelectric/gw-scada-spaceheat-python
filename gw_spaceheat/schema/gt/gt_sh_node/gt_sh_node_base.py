"""Base for gt.sh.node.110"""
import json
from typing import List, Optional, NamedTuple
from xmlrpc.client import Boolean
import schema.property_format as property_format
from schema.enums.role.role_map import Role, RoleMap


class GtShNodeBase(NamedTuple):
    ShNodeId: str 
    Alias: str     #
    Role: Role     #
    HasActor: Boolean
    ReportingSamplePeriodS: Optional[int] = None
    ComponentId: Optional[str] = None
    DisplayName: Optional[str] = None
    TypeAlias: str = 'gt.sh.node.110'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["ComponentId"] is None:
            del d["ComponentId"]
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["ReportingSamplePeriodS"] is None:
            del d["ReportingSamplePeriodS"]
        del(d["Role"])
        d["RoleGtEnumSymbol"] = RoleMap.local_to_gt(self.Role)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.Alias, str):
            errors.append(f"Alias {self.Alias} must have type str.")
        if not property_format.is_lrd_alias_format(self.Alias):
            errors.append(f"Alias {self.Alias}"
                          " must have format LrdAliasFormat")
        if self.ComponentId:
            if not isinstance(self.ComponentId, str):
                errors.append(f"ComponentId {self.ComponentId} must have type str.")
            if not property_format.is_uuid_canonical_textual(self.ComponentId):
                errors.append(f"ComponentId {self.ComponentId}"
                              " must have format UuidCanonicalTextual")
        if self.ReportingSamplePeriodS:
            if not isinstance(self.ReportingSamplePeriodS, int):
                errors.append(f"ReportingSamplePeriodS {self.ReportingSamplePeriodS} must have type int.")
        if not isinstance(self.HasActor, bool):
            errors.append(f"HasActor {self.HasActor} must hav etype bool")
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if not isinstance(self.Role, Role):
            errors.append(f"Role {self.Role} must have type {Role}.")
        if self.TypeAlias != 'gt.sh.node.110':
            errors.append(f"Type requires TypeAlias of gt.sh.node.110, not {self.TypeAlias}.")
  
        return errors
