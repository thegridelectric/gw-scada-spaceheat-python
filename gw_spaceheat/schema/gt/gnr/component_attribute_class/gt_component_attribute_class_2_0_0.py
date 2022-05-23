"""gt.component.attribute.class.200 type"""
from typing import List, Tuple, Optional
from schema.gt.gnr.component_attribute_class.gt_component_attribute_class_2_0_0_base import GtComponentAttributeClass200Base


class GtComponentAttributeClass200(GtComponentAttributeClass200Base):

    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.component.attribute.class.200 type.')
        return is_valid, errors

    # hand-code schema axiom validations below