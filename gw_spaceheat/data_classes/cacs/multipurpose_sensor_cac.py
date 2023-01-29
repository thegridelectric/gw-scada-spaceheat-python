"""MultipurposeSensorCac definition"""
from typing import Dict, Optional, List

from data_classes.component_attribute_class import ComponentAttributeClass
from schema.enums.make_model.make_model_map import MakeModelMap
from schema.enums.unit.unit_map import Unit, UnitMap
from gwproto.enums.telemetry_name.telemetry_name_map import TelemetryNameMap


class MultipurposeSensorCac(ComponentAttributeClass):
    by_id: Dict[str, "MultipurposeSensorCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        exponent: int,
        typical_response_time_ms: int,
        temp_unit_gt_enum_symbol: str,
        make_model_gt_enum_symbol: str,
        telemetry_name_list: List[str],
        max_thermistors: Optional[int],
        display_name: Optional[str] = None,
        comms_method: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            component_attribute_class_id=component_attribute_class_id, display_name=display_name
        )

        self.exponent = exponent
        self.comms_method = comms_method
        self.typical_response_time_ms = typical_response_time_ms
        self.max_thermistors = max_thermistors
        self.telemetry_name_list = [] 
        for enum_symbol in telemetry_name_list:
            self.telemetry_name_list.append(TelemetryNameMap.gt_to_local(enum_symbol))
        self.temp_unit = UnitMap.gt_to_local(temp_unit_gt_enum_symbol)
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)

        MultipurposeSensorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self
        if self.temp_unit not in [Unit.CELCIUS, Unit.FAHRENHEIT, Unit.UNITLESS]:
            raise Exception("TempSensorCac units must be Fahrenheit, Celsius or Unitless")

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
