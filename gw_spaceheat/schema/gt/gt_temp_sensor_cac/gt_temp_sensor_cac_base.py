"""Base for gt.temp.sensor.cac"""
import json
from typing import List, Optional, NamedTuple
import schema.property_format as property_format
from schema.enums.unit.unit_map import Unit, UnitMap
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtTempSensorCacBase(NamedTuple):
    ComponentAttributeClassId: str     #
    PrecisionExponent: int     #
    TypicalReadTimeMs: int     #
    TempUnit: Unit     #
    MakeModel: MakeModel     #
    DisplayName: Optional[str] = None
    CommsMethod: Optional[str] = None
    TypeAlias: str = 'gt.temp.sensor.cac.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["CommsMethod"] is None:
            del d["CommsMethod"]
        del(d["TempUnit"])
        d["TempUnitGtEnumSymbol"] = UnitMap.local_to_gt(self.TempUnit)
        del(d["MakeModel"])
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_gt(self.MakeModel)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if not isinstance(self.ComponentAttributeClassId, str):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId}"
                          " must have format UuidCanonicalTextual")
        if not isinstance(self.PrecisionExponent, int):
            errors.append(f"PrecisionExponent {self.PrecisionExponent} must have type int.")
        if self.CommsMethod:
            if not isinstance(self.CommsMethod, str):
                errors.append(f"CommsMethod {self.CommsMethod} must have type str.")
        if not isinstance(self.TypicalReadTimeMs, int):
            errors.append(f"TypicalReadTimeMs {self.TypicalReadTimeMs} must have type int.")
        if not isinstance(self.TempUnit, Unit):
            errors.append(f"TempUnit {self.TempUnit} must have type {Unit}.")
        if not isinstance(self.MakeModel, MakeModel):
            errors.append(f"MakeModel {self.MakeModel} must have type {MakeModel}.")
        if self.TypeAlias != 'gt.temp.sensor.cac.100':
            errors.append(f"Type requires TypeAlias of gt.temp.sensor.cac.100, not {self.TypeAlias}.")
        
        return errors
