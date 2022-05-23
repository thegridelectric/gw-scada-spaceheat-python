"""Base for gt.component.type.100"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format
from schema.gt.gnr.component_sub_category.gt_component_sub_category_1_0_0 import GtComponentSubCategory100


class GtComponentType100Base(NamedTuple):
    ComponentSubCategory: GtComponentSubCategory100     #
    IsResistiveLoad: bool     #
    Value: str     #
    DisplayName: Optional[str] = None
    ExpectedShutdownSeconds: Optional[int] = None
    ExpectedStartupSeconds: Optional[int] = None
    MpAlias: str = 'gt.component.type.100'

    def asdict(self):
        d = self._asdict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["ExpectedShutdownSeconds"] is None:
            del d["ExpectedShutdownSeconds"]
        if d["ExpectedStartupSeconds"] is None:
            del d["ExpectedStartupSeconds"]
        d['ComponentSubCategory'] = d['ComponentSubCategory'].asdict()
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.component.type.100':
            is_valid = False
            errors.append(f"Type requires MpAlias of gt.component.type.100, not {self.MpAlias}.")
        if not isinstance(self.IsResistiveLoad, bool):
            is_valid = False
            errors.append(f"IsResistiveLoad {self.IsResistiveLoad} must have type bool.")
        if not isinstance(self.Value, str):
            is_valid = False
            errors.append(f"Value {self.Value} must have type str.")
        if not isinstance(self.ComponentSubCategory, GtComponentSubCategory100):
            is_valid = False
            raise Exception(f"Make sure ComponentSubCategory has type GtComponentSubCategory100")
        new_is_valid, new_errors = self.ComponentSubCategory.is_valid()
        if not new_is_valid:
            is_valid = False
            errors += new_errors
        if self.DisplayName:
            if not isinstance(self.DisplayName, str):
                is_valid = False
                errors.append(f"DisplayName {self.DisplayName} must have type str.")
        if self.ExpectedShutdownSeconds:
            if not isinstance(self.ExpectedShutdownSeconds, int):
                is_valid = False
                errors.append(f"ExpectedShutdownSeconds {self.ExpectedShutdownSeconds} must have type int.")
        if self.ExpectedStartupSeconds:
            if not isinstance(self.ExpectedStartupSeconds, int):
                is_valid = False
                errors.append(f"ExpectedStartupSeconds {self.ExpectedStartupSeconds} must have type int.")
        return is_valid, errors

