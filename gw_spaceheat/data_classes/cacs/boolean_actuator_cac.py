"""BooleanActuatorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.boolean_actuator_cac_base import BooleanActuatorCacBase
from schema.gt.gt_boolean_actuator_cac.gt_boolean_actuator_cac import GtBooleanActuatorCac


class BooleanActuatorCac(BooleanActuatorCacBase):
    by_id: Dict[str, "BooleanActuatorCac"] = {}

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                             display_name=display_name,
                                             make_model_gt_enum_symbol=make_model_gt_enum_symbol,
                                             )
        BooleanActuatorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def _check_update_axioms(self, type: GtBooleanActuatorCac):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
