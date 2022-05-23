"""gt.component.attribute.class.1_1_0 Schema"""
from typing import List, Dict, Tuple, Optional
from schema.gt.gnr.component_attribute_class.gt_component_attribute_class_1_1_0_schema_base import SchemaBase


class GtComponentAttributeClass110(SchemaBase):
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()
        if len(errors) > 0:
            errors.insert(0, 'Errors making gt.component.attribute.class.1_1_0 type.')
        return is_valid, errors

    # hand-code schema axiom validations below