"""ElectricHeaterCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from schema.enums.make_model.make_model_map import MakeModelMap


class ElectricHeaterCac(ComponentAttributeClass):
    by_id: Dict[str, "ElectricHeaterCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model_gt_enum_symbol: str,
        display_name: Optional[str] = None,
    ):
        super(self.__class__, self,).__init__(
            component_attribute_class_id=component_attribute_class_id,
            display_name=display_name,
        )

        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)
        ElectricHeaterCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
