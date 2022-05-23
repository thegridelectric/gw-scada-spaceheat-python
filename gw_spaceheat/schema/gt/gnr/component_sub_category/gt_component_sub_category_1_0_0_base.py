"""Base for gt.component.sub.category.100"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format
from schema.gt.gnr.component_category.gt_component_category_1_0_0 import GtComponentCategory100


class GtComponentSubCategory100Base(NamedTuple):
    ComponentCategory: GtComponentCategory100     #
    Value: str     #
    MpAlias: str = 'gt.component.sub.category.100'

    def asdict(self):
        d = self._asdict()
        d['ComponentCategory'] = d['ComponentCategory'].asdict()
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.component.sub.category.100':
            is_valid = False
            errors.append(f"Type requires MpAlias of gt.component.sub.category.100, not {self.MpAlias}.")
        if not isinstance(self.Value, str):
            is_valid = False
            errors.append(f"Value {self.Value} must have type str.")
        if not isinstance(self.ComponentCategory, GtComponentCategory100):
            is_valid = False
            raise Exception(f"Make sure ComponentCategory has type GtComponentCategory100")
        new_is_valid, new_errors = self.ComponentCategory.is_valid()
        if not new_is_valid:
            is_valid = False
            errors += new_errors
        return is_valid, errors

