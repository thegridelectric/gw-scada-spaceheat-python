"""ElectricHeaterCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from schema.enums.make_model.make_model_map import MakeModelMap


class ResistiveHeaterCac(ComponentAttributeClass):
    by_id: Dict[str, "ResistiveHeaterCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model_gt_enum_symbol: str,
        nameplate_max_power_w: int,
        rated_voltage_v: int,
        display_name: Optional[str] = None,
    ):
        super(self.__class__, self,).__init__(
            component_attribute_class_id=component_attribute_class_id,
            display_name=display_name,
        )
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)
        self.nameplate_max_power_w = nameplate_max_power_w
        self.rated_voltage_v = rated_voltage_v
        ResistiveHeaterCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
