"""Base for gt.electric.meter.cac.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from schema.enums.local_comm_interface.local_comm_interface_map import (
    LocalCommInterface,
    LocalCommInterfaceMap,
)
from schema.enums.make_model.make_model_map import (
    MakeModel,
    MakeModelMap,
)


class GtElectricMeterCacBase(NamedTuple):
    ComponentAttributeClassId: str  #
    LocalCommInterface: LocalCommInterface  #
    MakeModel: MakeModel  #
    DisplayName: Optional[str] = None
    DefaultBaud: Optional[int] = None
    UpdatePeriodMs: Optional[int] = None
    TypeAlias: str = "gt.electric.meter.cac.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["LocalCommInterface"]
        d["LocalCommInterfaceGtEnumSymbol"] = LocalCommInterfaceMap.local_to_gt(self.LocalCommInterface)
        del d["MakeModel"]
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_gt(self.MakeModel)
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["DefaultBaud"] is None:
            del d["DefaultBaud"]
        if d["UpdatePeriodMs"] is None:
            del d["UpdatePeriodMs"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ComponentAttributeClassId, str):
            errors.append(
                f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            errors.append(
                f"ComponentAttributeClassId {self.ComponentAttributeClassId}"
                " must have format UuidCanonicalTextual"
            )
        if not isinstance(self.LocalCommInterface, LocalCommInterface):
            errors.append(
                f"LocalCommInterface {self.LocalCommInterface} must have type {LocalCommInterface}."
            )
        if not isinstance(self.MakeModel, MakeModel):
            errors.append(
                f"MakeModel {self.MakeModel} must have type {MakeModel}."
            )
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if self.DefaultBaud:
            if not isinstance(self.DefaultBaud, int):
                errors.append(
                    f"DefaultBaud {self.DefaultBaud} must have type int."
                )
        if self.UpdatePeriodMs:
            if not isinstance(self.UpdatePeriodMs, int):
                errors.append(
                    f"UpdatePeriodMs {self.UpdatePeriodMs} must have type int."
                )
        if self.TypeAlias != "gt.electric.meter.cac.100":
            errors.append(
                f"Type requires TypeAlias of gt.electric.meter.cac.100, not {self.TypeAlias}."
            )

        return errors
