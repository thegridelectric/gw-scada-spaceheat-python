"""TempSensorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.temp_sensor_cac_base import TempSensorCacBase
from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac import GtTempSensorCac
from schema.enums.units.units_map import Units

class TempSensorCac(TempSensorCacBase):
    by_id: Dict[str, "TempSensorCac"] = {}

    def __init__(self, component_attribute_class_id: str,
                 typical_read_time_ms: int,
                 temp_unit_gt_enum_symbol: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 precision_exponent: Optional[int] = None,
                 comms_method: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(display_name=display_name,
                                             component_attribute_class_id=component_attribute_class_id,
                                             precision_exponent=precision_exponent,
                                             comms_method=comms_method,
                                             typical_read_time_ms=typical_read_time_ms,
                                             temp_unit_gt_enum_symbol=temp_unit_gt_enum_symbol,
                                             make_model_gt_enum_symbol=make_model_gt_enum_symbol,
                                             )
        TempSensorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self
        if self.temp_unit not in [Units.CELCIUS, Units.FAHRENHEIT]:
            raise Exception(f"TempSensorCac units must be Fahrenheit or Celsius")

    def _check_update_axioms(self, type: GtTempSensorCac):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
