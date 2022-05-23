"""Base for gt.time.step.100"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format


class GtTimeStep100Base(NamedTuple):
    TimeStepId: str     #
    IrlCreatedAtUtc: float     #
    EraIndex: int     #
    EraId: str     #
    TsIndex: int     #
    PreviousTimeStepId: Optional[str] = None
    MpAlias: str = 'gt.time.step.100'

    def asdict(self):
        d = self._asdict()
        if d["PreviousTimeStepId"] is None:
            del d["PreviousTimeStepId"]
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.time.step.100':
            is_valid = False
            errors.append(f"Type requires MpAlias of gt.time.step.100, not {self.MpAlias}.")
        if not isinstance(self.TimeStepId, str):
            is_valid = False
            errors.append(f"TimeStepId {self.TimeStepId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.TimeStepId):
            is_valid = False
            errors.append(f"TimeStepId {self.TimeStepId} must have format UuidCanonicalTextual.")
        if not isinstance(self.IrlCreatedAtUtc, float):
            is_valid = False
            errors.append(f"IrlCreatedAtUtc {self.IrlCreatedAtUtc} must have type float.")
        if not isinstance(self.EraIndex, int):
            is_valid = False
            errors.append(f"EraIndex {self.EraIndex} must have type int.")
        if not isinstance(self.EraId, str):
            is_valid = False
            errors.append(f"EraId {self.EraId} must have type str.")
        if not schema.property_format.is_uuid_canonical_textual(self.EraId):
            is_valid = False
            errors.append(f"EraId {self.EraId} must have format UuidCanonicalTextual.")
        if not isinstance(self.TsIndex, int):
            is_valid = False
            errors.append(f"TsIndex {self.TsIndex} must have type int.")
        if not schema.property_format.is_non_negative_int64(self.TsIndex):
            is_valid = False
            errors.append(f"TsIndex {self.TsIndex} must have format NonNegativeInt64.")
        if self.PreviousTimeStepId:
            if not isinstance(self.PreviousTimeStepId, str):
                is_valid = False
                errors.append(f"PreviousTimeStepId {self.PreviousTimeStepId} must have type str.")
            if not schema.property_format.is_uuid_canonical_textual(self.PreviousTimeStepId):
                is_valid = False
                errors.append(f"PreviousTimeStepId {self.PreviousTimeStepId} must have format UuidCanonicalTextual.")
        return is_valid, errors

