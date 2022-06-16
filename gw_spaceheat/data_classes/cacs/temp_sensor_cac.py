"""TempSensorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.temp_sensor_cac_base import TempSensorCacBase
from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac import GtTempSensorCac
from schema.enums.unit.unit_map import Unit
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName

class TempSensorCac(TempSensorCacBase):
    by_id: Dict[str, "TempSensorCac"] = {}

    def __init__(self, component_attribute_class_id: str,
                 precision_exponent: int,
                 typical_read_time_ms: int,
                 temp_unit_gt_enum_symbol: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
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
        if self.temp_unit not in [Unit.CELCIUS, Unit.FAHRENHEIT]:
            raise Exception("TempSensorCac units must be Fahrenheit or Celsius")
        self.telemetry_name

    def _check_update_axioms(self, type: GtTempSensorCac):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"

    @property
    def telemetry_name(self):
        if self.precision_exponent == 3 and self.temp_unit == Unit.CELCIUS:
            return TelemetryName.WATER_TEMP_C_TIMES1000
        elif self.precision_exponent == 3 and self.temp_unit == Unit.FAHRENHEIT:
            return TelemetryName.WATER_TEMP_F_TIMES1000
        else:
            raise Exception(f'No Telemetry name for {self}')
