"""Base for pipe.flow.sensor.cac.gt.000"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.enums import (
    MakeModel,
    MakeModelMap,
)


class PipeFlowSensorCacGtBase(NamedTuple):
    ComponentAttributeClassId: str  #
    MakeModel: MakeModel  #
    DisplayName: Optional[str] = None
    CommsMethod: Optional[str] = None
    TypeAlias: str = "pipe.flow.sensor.cac.gt.000"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["CommsMethod"] is None:
            del d["CommsMethod"]
        del d["MakeModel"]
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_gt(self.MakeModel)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
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
        if self.CommsMethod:
            if not isinstance(self.CommsMethod, str):
                errors.append(
                    f"CommsMethod {self.CommsMethod} must have type str."
                )
        if not isinstance(self.MakeModel, MakeModel):
            errors.append(
                f"MakeModel {self.MakeModel} must have type {MakeModel}."
            )
        if self.TypeAlias != "pipe.flow.sensor.cac.gt.000":
            errors.append(
                f"Type requires TypeAlias of pipe.flow.sensor.cac.gt.000, not {self.TypeAlias}."
            )

        return errors