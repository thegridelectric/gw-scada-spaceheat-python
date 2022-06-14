"""ElectricMeterComponent definition"""
from typing import Dict, Optional

from data_classes.component import Component
from data_classes.components.electric_meter_component_base import ElectricMeterComponentBase
from schema.gt.gt_electric_meter_component.gt_electric_meter_component import GtElectricMeterComponent


class ElectricMeterComponent(ElectricMeterComponentBase):
    by_id: Dict[str, "ElectricMeterComponent"] =  {}

    def __init__(self, component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str] = None,
                 hw_uid: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(display_name=display_name,
                                             component_id=component_id,
                                             hw_uid=hw_uid,
                                             component_attribute_class_id=component_attribute_class_id,
                                             )
        ElectricMeterComponent.by_id[self.component_id] = self
        Component.by_id[self.component_id] = self

    def _check_update_axioms(self, type: GtElectricMeterComponent):
        pass

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
