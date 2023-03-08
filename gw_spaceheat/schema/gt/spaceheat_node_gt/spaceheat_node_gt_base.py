"""Base for spaceheat.node.gt.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from enums import (
    Role,
    RoleMap,
)
from enums import (
    ActorClass,
    ActorClassMap,
)


class SpaceheatNodeGtBase(NamedTuple):
    Alias: str  #
    Role: Role  #
    ActorClass: ActorClass  #
    ShNodeId: str  #
    ReportingSamplePeriodS: Optional[int] = None
    ComponentId: Optional[str] = None
    RatedVoltageV: Optional[int] = None
    DisplayName: Optional[str] = None
    TypicalVoltageV: Optional[int] = None
    TypeAlias: str = "spaceheat.node.gt.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["ReportingSamplePeriodS"] is None:
            del d["ReportingSamplePeriodS"]
        del d["Role"]
        d["RoleGtEnumSymbol"] = RoleMap.local_to_gt(self.Role)
        if d["ComponentId"] is None:
            del d["ComponentId"]
        if d["RatedVoltageV"] is None:
            del d["RatedVoltageV"]
        del d["ActorClass"]
        d["ActorClassGtEnumSymbol"] = ActorClassMap.local_to_gt(self.ActorClass)
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["TypicalVoltageV"] is None:
            del d["TypicalVoltageV"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.Alias, str):
            errors.append(
                f"Alias {self.Alias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.Alias):
            errors.append(
                f"Alias {self.Alias}"
                " must have format LrdAliasFormat"
            )
        if self.ReportingSamplePeriodS:
            if not isinstance(self.ReportingSamplePeriodS, int):
                errors.append(
                    f"ReportingSamplePeriodS {self.ReportingSamplePeriodS} must have type int."
                )
        if not isinstance(self.Role, Role):
            errors.append(
                f"Role {self.Role} must have type {Role}."
            )
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
        if self.RatedVoltageV:
            if not isinstance(self.RatedVoltageV, int):
                errors.append(
                    f"RatedVoltageV {self.RatedVoltageV} must have type int."
                )
            if not property_format.is_positive_integer(self.RatedVoltageV):
                errors.append(
                    f"RatedVoltageV {self.RatedVoltageV}"
                    " must have format PositiveInteger"
                )
        if not isinstance(self.ActorClass, ActorClass):
            errors.append(
                f"ActorClass {self.ActorClass} must have type {ActorClass}."
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
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if self.TypicalVoltageV:
            if not isinstance(self.TypicalVoltageV, int):
                errors.append(
                    f"TypicalVoltageV {self.TypicalVoltageV} must have type int."
                )
            if not property_format.is_positive_integer(self.TypicalVoltageV):
                errors.append(
                    f"TypicalVoltageV {self.TypicalVoltageV}"
                    " must have format PositiveInteger"
                )
        if self.TypeAlias != "spaceheat.node.gt.100":
            errors.append(
                f"Type requires TypeAlias of spaceheat.node.gt.100, not {self.TypeAlias}."
            )

        return errors
