"""Base for gt.component.category.100"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format


class GtComponentCategory100Base(NamedTuple):
    Value: str     #
    Description: str     #
    MpAlias: str = 'gt.component.category.100'

    def asdict(self):
        d = self._asdict()
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.component.category.100':
            is_valid = False
            errors.append(f"Type requires MpAlias of gt.component.category.100, not {self.MpAlias}.")
        if not isinstance(self.Value, str):
            is_valid = False
            errors.append(f"Value {self.Value} must have type str.")
        if not isinstance(self.Description, str):
            is_valid = False
            errors.append(f"Description {self.Description} must have type str.")
        return is_valid, errors

