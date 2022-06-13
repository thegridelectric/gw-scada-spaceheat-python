"""Base for gt.sh.node"""
import json
from typing import List, Optional, NamedTuple
import schema.property_format as property_format
from schema.enums.role.role_map import Role, RoleMap


class GtShNodeBase(NamedTuple):
    ShNodeId: str 
    Alias: str     #
    Role: Role     #
    PrimaryComponentId: Optional[str] = None
    DisplayName: Optional[str] = None
    PythonActorName: Optional[str] = None
    TypeAlias: str = 'gt.sh.node.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["PrimaryComponentId"] is None:
            del d["PrimaryComponentId"]
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["PythonActorName"] is None:
            del d["PythonActorName"]
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
        if self.PrimaryComponentId:
            if not isinstance(self.PrimaryComponentId, str):
                errors.append(f"PrimaryComponentId {self.PrimaryComponentId} must have type str.")
            if not property_format.is_uuid_canonical_textual(self.PrimaryComponentId):
                errors.append(f"PrimaryComponentId {self.PrimaryComponentId}"
                                " must have format UuidCanonicalTextual")
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if self.PythonActorName:
            if not isinstance(self.PythonActorName, str):
                errors.append(f"PythonActorName {self.PythonActorName} must have type str.")
        if not isinstance(self.Role, Role):
            errors.append(f"Role {self.Role} must have type {Role}.")
        if self.TypeAlias != 'gt.sh.node.100':
            errors.append(f"Type requires TypeAlias of gt.sh.node.100, not {self.TypeAlias}.")
        
        return errors
