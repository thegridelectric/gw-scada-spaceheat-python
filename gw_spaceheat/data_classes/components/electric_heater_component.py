"""ElectricHeaterComponent definition"""
from typing import Dict, Optional

from data_classes.components.electric_heater_component_base import ElectricHeaterComponentBase
from schema.gt.gt_electric_heater_component.gt_electric_heater_component_100 import GtElectricHeaterComponent100


class ElectricHeaterComponent(ElectricHeaterComponentBase):
    by_id: Dict[str, ElectricHeaterComponentBase] =  ElectricHeaterComponentBase._by_id

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

    def _check_update_axioms(self, type: GtElectricHeaterComponent100):
        pass

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
