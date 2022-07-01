"""Base for gt.sh.node.120"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.enums.actor_class.actor_class_map import (
    ActorClass,
    ActorClassMap,
)
from schema.enums.role.role_map import (
    Role,
    RoleMap,
)


class GtShNodeBase(NamedTuple):
    ActorClass: ActorClass  #
    Role: Role  #
    ShNodeId: str  #
    Alias: str  #
    ComponentId: Optional[str] = None
    DisplayName: Optional[str] = None
    ReportingSamplePeriodS: Optional[int] = None
    TypeAlias: str = "gt.sh.node.120"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["ComponentId"] is None:
            del d["ComponentId"]
        if d["DisplayName"] is None:
            del d["DisplayName"]
        del d["ActorClass"]
        d["ActorClassGtEnumSymbol"] = ActorClassMap.local_to_gt(self.ActorClass)
        del d["Role"]
        d["RoleGtEnumSymbol"] = RoleMap.local_to_gt(self.Role)
        if d["ReportingSamplePeriodS"] is None:
            del d["ReportingSamplePeriodS"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.ComponentId:
            if not isinstance(self.ComponentId, str):
                errors.append(
                    f"ComponentId {self.ComponentId} must have type str."
                )
            if not property_format.is_uuid_canonical_textual(self.ComponentId):
                errors.append(
                    f"ComponentId {self.ComponentId}"
                    " must have format UuidCanonicalTextual"
                )
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if not isinstance(self.ActorClass, ActorClass):
            errors.append(
                f"ActorClass {self.ActorClass} must have type {ActorClass}."
            )
        if not isinstance(self.Role, Role):
            errors.append(
                f"Role {self.Role} must have type {Role}."
            )
        if self.ReportingSamplePeriodS:
            if not isinstance(self.ReportingSamplePeriodS, int):
                errors.append(
                    f"ReportingSamplePeriodS {self.ReportingSamplePeriodS} must have type int."
                )
        if not isinstance(self.ShNodeId, str):
            errors.append(
                f"ShNodeId {self.ShNodeId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ShNodeId):
            errors.append(
                f"ShNodeId {self.ShNodeId}"
                " must have format UuidCanonicalTextual"
            )
        if not isinstance(self.Alias, str):
            errors.append(
                f"Alias {self.Alias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.Alias):
            errors.append(
                f"Alias {self.Alias}"
                " must have format LrdAliasFormat"
            )
        if self.TypeAlias != "gt.sh.node.120":
            errors.append(
                f"Type requires TypeAlias of gt.sh.node.120, not {self.TypeAlias}."
            )

        return errors
