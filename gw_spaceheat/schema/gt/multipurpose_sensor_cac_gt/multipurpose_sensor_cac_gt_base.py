"""Base for multipurpose.sensor.cac.gt.000"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.enums import (
    TelemetryName,
    TelemetryNameMap,
)
from schema.enums import (
    Unit,
    UnitMap,
)
from schema.enums import (
    MakeModel,
    MakeModelMap,
)


class MultipurposeSensorCacGtBase(NamedTuple):
    TelemetryNameList: List[TelemetryName]  #
    TempUnit: Unit  #
    MakeModel: MakeModel  #
    ComponentAttributeClassId: str  #
    Exponent: int  #
    PollPeriodMs: int  #
    MaxThermistors: Optional[int] = None #
    DisplayName: Optional[str] = None
    CommsMethod: Optional[str] = None
    TypeAlias: str = "multipurpose.sensor.cac.gt.000"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.TelemetryNameList:
            telemetry_name_list.append(TelemetryNameMap.local_to_gt(elt))
        d["TelemetryNameList"] = telemetry_name_list
        if d["DisplayName"] is None:
            del d["DisplayName"]
        del d["TempUnit"]
        d["TempUnitGtEnumSymbol"] = UnitMap.local_to_gt(self.TempUnit)
        del d["MakeModel"]
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_gt(self.MakeModel)
        if d["CommsMethod"] is None:
            del d["CommsMethod"]
        if d["MaxThermistors"] is None:
            del d["MaxThermistors"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.TelemetryNameList, list):
            errors.append(
                f"TelemetryNameList {self.TelemetryNameList} must have type list."
            )
        else:
            for elt in self.TelemetryNameList:
                if not isinstance(elt, TelemetryName):
                    errors.append(
                        f"elt {elt} of TelemetryNameList must have type TelemetryName."
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
        if not isinstance(self.PollPeriodMs, int):
            errors.append(
                f"PollPeriodMs {self.PollPeriodMs} must have type int."
            )
        if self.MaxThermistors:
            if not isinstance(self.MaxThermistors, int):
                errors.append(
                    f"PollPeriodMs {self.MaxThermistors} must have type int."
                )
        if self.TypeAlias != "multipurpose.sensor.cac.gt.000":
            errors.append(
                f"Type requires TypeAlias of multipurpose.sensor.cac.gt.000, not {self.TypeAlias}."
            )

        return errors
