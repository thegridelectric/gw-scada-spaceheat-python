"""Base for gt.temp.sensor.cac.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)
from schema.enums.unit.unit_map import (
    Unit,
    UnitMap,
)
from schema.enums.make_model.make_model_map import (
    MakeModel,
    MakeModelMap,
)


class GtTempSensorCacBase(NamedTuple):
    TelemetryName: TelemetryName  #
    TempUnit: Unit  #
    MakeModel: MakeModel  #
    ComponentAttributeClassId: str  #
    Exponent: int  #
    TypicalResponseTimeMs: int  #
    DisplayName: Optional[str] = None
    CommsMethod: Optional[str] = None
    TypeAlias: str = "gt.temp.sensor.cac.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["TelemetryName"]
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        if d["DisplayName"] is None:
            del d["DisplayName"]
        del d["TempUnit"]
        d["TempUnitGtEnumSymbol"] = UnitMap.local_to_gt(self.TempUnit)
        del d["MakeModel"]
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_gt(self.MakeModel)
        if d["CommsMethod"] is None:
            del d["CommsMethod"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(
                f"TelemetryName {self.TelemetryName} must have type {TelemetryName}."
            )
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if not isinstance(self.TempUnit, Unit):
            errors.append(
                f"TempUnit {self.TempUnit} must have type {Unit}."
            )
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
        if not isinstance(self.Exponent, int):
            errors.append(
                f"Exponent {self.Exponent} must have type int."
            )
        if self.CommsMethod:
            if not isinstance(self.CommsMethod, str):
                errors.append(
                    f"CommsMethod {self.CommsMethod} must have type str."
                )
        if not isinstance(self.TypicalResponseTimeMs, int):
            errors.append(
                f"TypicalResponseTimeMs {self.TypicalResponseTimeMs} must have type int."
            )
        if self.TypeAlias != "gt.temp.sensor.cac.100":
            errors.append(
                f"Type requires TypeAlias of gt.temp.sensor.cac.100, not {self.TypeAlias}."
            )

        return errors
