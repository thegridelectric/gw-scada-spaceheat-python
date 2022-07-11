"""Base for resistive.heater.component.gt.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format


class ResistiveHeaterComponentGtBase(NamedTuple):
    ComponentAttributeClassId: str
    ComponentId: str  #
    DisplayName: Optional[str] = None
    TestedMaxHotMilliOhms: Optional[int] = None
    HwUid: Optional[str] = None
    TestedMaxColdMilliOhms: Optional[int] = None
    TypeAlias: str = "resistive.heater.component.gt.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["TestedMaxHotMilliOhms"] is None:
            del d["TestedMaxHotMilliOhms"]
        if d["HwUid"] is None:
            del d["HwUid"]
        if d["TestedMaxColdMilliOhms"] is None:
            del d["TestedMaxColdMilliOhms"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
                )
        if self.TestedMaxHotMilliOhms:
            if not isinstance(self.TestedMaxHotMilliOhms, int):
                errors.append(
                    f"TestedMaxHotMilliOhms {self.TestedMaxHotMilliOhms} must have type int."
                )
            if not property_format.is_positive_integer(self.TestedMaxHotMilliOhms):
                errors.append(
                    f"TestedMaxHotMilliOhms {self.TestedMaxHotMilliOhms}"
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
        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(
                    f"HwUid {self.HwUid} must have type str."
                )
        if not isinstance(self.ComponentId, str):
            errors.append(
                f"ComponentId {self.ComponentId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ComponentId):
            errors.append(
                f"ComponentId {self.ComponentId}"
                " must have format UuidCanonicalTextual"
            )
        if self.TestedMaxColdMilliOhms:
            if not isinstance(self.TestedMaxColdMilliOhms, int):
                errors.append(
                    f"TestedMaxColdMilliOhms {self.TestedMaxColdMilliOhms} must have type int."
                )
            if not property_format.is_positive_integer(self.TestedMaxColdMilliOhms):
                errors.append(
                    f"TestedMaxColdMilliOhms {self.TestedMaxColdMilliOhms}"
                    " must have format PositiveInteger"
                )
        if self.TypeAlias != "resistive.heater.component.gt.100":
            errors.append(
                f"Type requires TypeAlias of resistive.heater.component.gt.100, not {self.TypeAlias}."
            )

        return errors
