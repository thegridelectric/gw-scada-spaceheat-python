"""Base for gt.boolean.actuator.component.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format


class GtBooleanActuatorComponentBase(NamedTuple):
    ComponentAttributeClassId: str
    ComponentId: str  #
    DisplayName: Optional[str] = None
    Gpio: Optional[int] = None
    HwUid: Optional[str] = None
    TypeAlias: str = "gt.boolean.actuator.component.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["Gpio"] is None:
            del d["Gpio"]
        if d["HwUid"] is None:
            del d["HwUid"]
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
        if not isinstance(self.ComponentId, str):
            errors.append(
                f"ComponentId {self.ComponentId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ComponentId):
            errors.append(
                f"ComponentId {self.ComponentId}"
                " must have format UuidCanonicalTextual"
            )
        if self.Gpio:
            if not isinstance(self.Gpio, int):
                errors.append(
                    f"Gpio {self.Gpio} must have type int."
                )
        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(
                    f"HwUid {self.HwUid} must have type str."
                )
        if self.TypeAlias != "gt.boolean.actuator.component.100":
            errors.append(
                f"Type requires TypeAlias of gt.boolean.actuator.component.100, not {self.TypeAlias}."
            )

        return errors
