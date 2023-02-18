"""Base for pipe.flow.sensor.component.gt.000"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format


class PipeFlowSensorComponentGtBase(NamedTuple):
    ComponentId: str  #
    ComponentAttributeClassId: str
    I2cAddress: int
    DisplayName: Optional[str] = None
    HwUid: Optional[str] = None
    TypeAlias: str = "pipe.flow.sensor.component.gt.000"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["HwUid"] is None:
            del d["HwUid"]
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ComponentId, str):
            errors.append(
                f"ComponentId {self.ComponentId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.ComponentId):
            errors.append(
                f"ComponentId {self.ComponentId}"
                " must have format UuidCanonicalTextual"
            )
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
        if not isinstance(self.I2cAddress, int):
            errors.append(
                f"I2cAddress {self.I2cAddress} must have type int."
            )
        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(
                    f"HwUid {self.HwUid} must have type str."
                )
        if self.TypeAlias != "pipe.flow.sensor.component.gt.000":
            errors.append(
                f"Type requires TypeAlias of pipe.flow.sensor.component.gt.000, not {self.TypeAlias}."
            )

        return errors
