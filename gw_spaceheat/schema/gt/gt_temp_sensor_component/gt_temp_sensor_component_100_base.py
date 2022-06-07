"""Base for gt.temp.sensor.component.100"""
from typing import List, Optional, NamedTuple
import schema.property_format as property_format


class GtTempSensorComponent100Base(NamedTuple):
    ComponentId: str     #
    ComponentAttributeClassId: str
    DisplayName: Optional[str] = None
    HwUid: Optional[str] = None
    Alias: str = 'gt.temp.sensor.component.100'

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
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
        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(f"HwUid {self.HwUid} must have type str.")
        if not isinstance(self.ComponentAttributeClassId, str):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId}"
                          " must have format UuidCanonicalTextual")
        if self.Alias != 'gt.temp.sensor.component.100':
            errors.append(f"Type requires Alias of gt.temp.sensor.component.100, not {self.Alias}.")

        return errors
