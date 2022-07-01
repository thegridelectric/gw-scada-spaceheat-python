"""ElectricHeaterComponent definition"""
from typing import Dict, Optional

from data_classes.cacs.electric_heater_cac import ElectricHeaterCac
from data_classes.component import Component
from schema.enums.make_model.make_model_map import MakeModel


class ElectricHeaterComponent(Component):
    by_id: Dict[str, "ElectricHeaterComponent"] = {}

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        hw_uid: Optional[str] = None,
        display_name: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            display_name=display_name,
            component_id=component_id,
            hw_uid=hw_uid,
            component_attribute_class_id=component_attribute_class_id,
        )
        ElectricHeaterComponent.by_id[self.component_id] = self
        Component.by_id[self.component_id] = self

    @property
    def cac(self) -> ElectricHeaterCac:
        return ElectricHeaterCac.by_id[self.component_attribute_class_id]

    @property
    def make_model(self) -> MakeModel:
        return self.cac.make_model

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
