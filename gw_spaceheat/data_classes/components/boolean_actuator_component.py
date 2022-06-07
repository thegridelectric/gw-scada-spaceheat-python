"""BooleanActuatorComponent definition"""
from typing import Dict, Optional

from data_classes.components.boolean_actuator_component_base import BooleanActuatorComponentBase
from schema.gt.gt_boolean_actuator_component.gt_boolean_actuator_component_100 import GtBooleanActuatorComponent100


class BooleanActuatorComponent(BooleanActuatorComponentBase):
    by_id: Dict[str, BooleanActuatorComponentBase] = BooleanActuatorComponentBase._by_id

    def __init__(self, component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str] = None,
                 gpio: Optional[int] = None,
                 hw_uid: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(display_name=display_name,
                                             component_id=component_id,
                                             gpio=gpio,
                                             hw_uid=hw_uid,
                                             component_attribute_class_id=component_attribute_class_id,
                                             )

    def _check_update_axioms(self, type: GtBooleanActuatorComponent100):
        pass

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
