"""Base for gt.boolean.actuator.component.100"""
from typing import List, Optional, NamedTuple
import schema.property_format as property_format


class GtBooleanActuatorComponent100Base(NamedTuple):
    ComponentId: str     #
    ComponentAttributeClassId: str
    DisplayName: Optional[str] = None
    Gpio: Optional[int] = None
    HwUid: Optional[str] = None
    Alias: str = 'gt.boolean.actuator.component.100'

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
                errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if not isinstance(self.ComponentId, str):
            errors.append(f"ComponentId {self.ComponentId} must have type str.")
        if not property_format.is_uuid_canonical_textual(self.ComponentId):
            errors.append(f"ComponentId {self.ComponentId}"
                          " must have format UuidCanonicalTextual")
        if self.Gpio:
            if not isinstance(self.Gpio, int):
                errors.append(f"Gpio {self.Gpio} must have type int.")
        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(f"HwUid {self.HwUid} must have type str.")
        if not isinstance(self.ComponentAttributeClassId, str):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId}"
                          " must have format UuidCanonicalTextual")
        if self.Alias != 'gt.boolean.actuator.component.100':
            errors.append(f"Type requires Alias of gt.boolean.actuator.component.100, not {self.Alias}.")

        return errors
