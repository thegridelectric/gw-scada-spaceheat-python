"""Base for gt.boolean.actuator.cac.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.enums.make_model.make_model_map import (
    MakeModel,
    MakeModelMap,
)


class GtBooleanActuatorCacBase(NamedTuple):
    MakeModel: MakeModel  #
    ComponentAttributeClassId: str  #
    TypicalResponseTimeMs: int  #
    DisplayName: Optional[str] = None
    TypeAlias: str = "gt.boolean.actuator.cac.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["MakeModel"]
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_gt(self.MakeModel)
        if d["DisplayName"] is None:
            del d["DisplayName"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.MakeModel, MakeModel):
            errors.append(
                f"MakeModel {self.MakeModel} must have type {MakeModel}."
            )
        if not isinstance(self.ComponentAttributeClassId, str):
            errors.append(
                f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            errors.append(
                f"ComponentAttributeClassId {self.ComponentAttributeClassId}"
                " must have format UuidCanonicalTextual"
            )
        if not isinstance(self.TypicalResponseTimeMs, int):
            errors.append(
                f"TypicalResponseTimeMs {self.TypicalResponseTimeMs} must have type int."
            )
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if self.TypeAlias != "gt.boolean.actuator.cac.100":
            errors.append(
                f"Type requires TypeAlias of gt.boolean.actuator.cac.100, not {self.TypeAlias}."
            )

        return errors
