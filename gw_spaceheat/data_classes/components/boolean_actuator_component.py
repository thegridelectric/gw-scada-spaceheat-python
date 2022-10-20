"""BooleanActuatorComponent definition"""
from typing import Dict, Optional

from data_classes.cacs.boolean_actuator_cac import BooleanActuatorCac
from data_classes.component import Component
from schema.enums import MakeModel


class BooleanActuatorComponent(Component):
    by_id: Dict[str, "BooleanActuatorComponent"] = {}

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        display_name: Optional[str] = None,
        gpio: Optional[int] = None,
        hw_uid: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            display_name=display_name,
            component_id=component_id,
            hw_uid=hw_uid,
            component_attribute_class_id=component_attribute_class_id,
        )
        self.gpio = gpio

        BooleanActuatorComponent.by_id[self.component_id] = self
        Component.by_id[self.component_id] = self

    @property
    def cac(self) -> BooleanActuatorCac:
        return BooleanActuatorCac.by_id[self.component_attribute_class_id]

    @property
    def make_model(self) -> MakeModel:
        return self.cac.make_model

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
