"""Base for gt.component.100"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format


class GtComponent100Base(NamedTuple):
    DisplayName: str     #
    ComponentId: str     #
    ComponentAttributeClassId: str     #
    MpAlias: str = 'gt.component.100'

    def asdict(self):
        d = self._asdict()
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.component.100':
            is_valid = False
            errors.append(f"Type requires MpAlias of gt.component.100, not {self.MpAlias}.")
        if not isinstance(self.DisplayName, str):
            is_valid = False
            errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if not isinstance(self.ComponentId, str):
            is_valid = False
            errors.append(f"ComponentId {self.ComponentId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.ComponentId):
            is_valid = False
            errors.append(f"ComponentId {self.ComponentId} must have format UuidCanonicalTextual.")
        if not isinstance(self.ComponentAttributeClassId, str):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.ComponentAttributeClassId):
            is_valid = False
            errors.append(f"ComponentAttributeClassId {self.ComponentAttributeClassId} must have format UuidCanonicalTextual.")
        return is_valid, errors

