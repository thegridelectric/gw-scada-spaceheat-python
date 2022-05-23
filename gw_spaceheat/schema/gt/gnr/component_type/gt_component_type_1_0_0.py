"""gt.component.type.100 type"""
from typing import List, Tuple, Optional
from schema.gt.gnr.component_type.gt_component_type_1_0_0_base import GtComponentType100Base


class GtComponentType100(GtComponentType100Base):

    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.component.type.100 type.')
        return is_valid, errors

    # hand-code schema axiom validations below