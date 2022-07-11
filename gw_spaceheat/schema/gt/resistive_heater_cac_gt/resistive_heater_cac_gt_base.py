"""Base for resistive.heater.cac.gt.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.enums.make_model.make_model_map import (
    MakeModel,
    MakeModelMap,
)


class ResistiveHeaterCacGtBase(NamedTuple):
    MakeModel: MakeModel  #
    RatedVoltageV: int  #
    NameplateMaxPowerW: int  #
    ComponentAttributeClassId: str  #
    DisplayName: Optional[str] = None
    TypeAlias: str = "resistive.heater.cac.gt.100"

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
        if not isinstance(self.RatedVoltageV, int):
            errors.append(
                f"RatedVoltageV {self.RatedVoltageV} must have type int."
            )
        if not property_format.is_positive_integer(self.RatedVoltageV):
            errors.append(
                f"RatedVoltageV {self.RatedVoltageV}"
                " must have format PositiveInteger"
            )
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if not isinstance(self.NameplateMaxPowerW, int):
            errors.append(
                f"NameplateMaxPowerW {self.NameplateMaxPowerW} must have type int."
            )
        if not property_format.is_positive_integer(self.NameplateMaxPowerW):
            errors.append(
                f"NameplateMaxPowerW {self.NameplateMaxPowerW}"
                " must have format PositiveInteger"
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
        if self.TypeAlias != "resistive.heater.cac.gt.100":
            errors.append(
                f"Type requires TypeAlias of resistive.heater.cac.gt.100, not {self.TypeAlias}."
            )

        return errors
