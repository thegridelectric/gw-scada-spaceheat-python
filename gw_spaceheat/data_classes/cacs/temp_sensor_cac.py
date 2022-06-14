"""TempSensorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.temp_sensor_cac_base import TempSensorCacBase
from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac import GtTempSensorCac


class TempSensorCac(TempSensorCacBase):
    by_id: Dict[str, "TempSensorCac"] = {}

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 temp_unit: Optional[str] = None,
                 precision_exponent: Optional[int] = None,
                 comms_method: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(display_name=display_name,
                                             temp_unit=temp_unit,
                                             component_attribute_class_id=component_attribute_class_id,
                                             precision_exponent=precision_exponent,
                                             comms_method=comms_method,
                                             make_model_gt_enum_symbol=make_model_gt_enum_symbol,
                                             )
        TempSensorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def _check_update_axioms(self, type: GtTempSensorCac):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
