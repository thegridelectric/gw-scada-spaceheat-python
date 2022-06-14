"""ElectricHeaterComponent definition"""
from typing import Dict, Optional

from data_classes.component import Component
from data_classes.components.electric_heater_component_base import ElectricHeaterComponentBase
from schema.gt.gt_electric_heater_component.gt_electric_heater_component import GtElectricHeaterComponent


class ElectricHeaterComponent(ElectricHeaterComponentBase):
    by_id: Dict[str, "ElectricHeaterComponent"] =  {}

    def __init__(self, component_id: str,
                 component_attribute_class_id: str,
                 hw_uid: Optional[str] = None,
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(hw_uid=hw_uid,
                                             display_name=display_name,
                                             component_id=component_id,
                                             component_attribute_class_id=component_attribute_class_id,
                                             )
        ElectricHeaterComponent.by_id[self.component_id] = self
        Component.by_id[self.component_id] = self

    def _check_update_axioms(self, type: GtElectricHeaterComponent):
        pass

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
