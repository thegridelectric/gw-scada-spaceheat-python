"""Base for gt.electric.meter.component.100"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format


class GtElectricMeterComponentBase(NamedTuple):
    ComponentAttributeClassId: str
    ComponentId: str  #
    DisplayName: Optional[str] = None
    HwUid: Optional[str] = None
    ModbusHost: Optional[str] = None
    ModbusPort: Optional[int] = None
    ModbusPowerRegister: Optional[int] = None
    ModbusHwUidRegister: Optional[int] = None
    TypeAlias: str = "gt.electric.meter.component.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["HwUid"] is None:
            del d["HwUid"]
        if d["ModbusPowerRegister"] is None:
            del d["ModbusPowerRegister"]
        if d["ModbusHost"] is None:
            del d["ModbusHost"]
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
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                errors.append(
                    f"DisplayName {self.DisplayName} must have type str."
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
        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(
                    f"HwUid {self.HwUid} must have type str."
                )
        if self.ModbusHost:
            if not isinstance(self.ModbusHost, str):
                errors.append(
                    f"ModbusHost {self.ModbusHost} must have type str."
                )
        if self.ModbusPort:
            if not isinstance(self.ModbusPort, int):
                errors.append(
                    f"ModbusPort {self.ModbusPort} must have type int."
                )
        if self.ModbusPowerRegister:
            if not isinstance(self.ModbusPowerRegister, int):
                errors.append(
                    f"ModbusPowerRegister {self.ModbusPowerRegister} must have type int."
                )
        if self.ModbusHwUidRegister:
            if not isinstance(self.ModbusHwUidRegister, int):
                errors.append(
                    f"ModbusHwUidRegister {self.ModbusHwUidRegister} must have type int."
                )
        if self.TypeAlias != "gt.electric.meter.component.100":
            errors.append(
                f"Type requires TypeAlias of gt.electric.meter.component.100, not {self.TypeAlias}."
            )

        return errors
