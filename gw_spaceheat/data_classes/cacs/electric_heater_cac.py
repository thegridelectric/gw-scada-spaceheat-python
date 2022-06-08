"""ElectricHeaterCac definition"""
from typing import Dict, Optional

from data_classes.cacs.electric_heater_cac_base import ElectricHeaterCacBase
from schema.gt.gt_electric_heater_cac.gt_electric_heater_cac_100 import GtElectricHeaterCac100


class ElectricHeaterCac(ElectricHeaterCacBase):
    by_id: Dict[str, ElectricHeaterCacBase] = ElectricHeaterCacBase._by_id

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                             display_name=display_name,
                                             make_model_gt_enum_symbol=make_model_gt_enum_symbol,
                                             )

    def _check_update_axioms(self, type: GtElectricHeaterCac100):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
