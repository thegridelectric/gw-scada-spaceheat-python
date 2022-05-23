"""gt.component.1_1_0 Schema"""
from typing import List, Dict, Tuple, Optional
from schema.gt.gnr.component.gt_component_1_1_0_schema_base import SchemaBase


class GtComponent110(SchemaBase):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.component.1_1_0 type.')
        return is_valid, errors

    # hand-code schema axiom validations below