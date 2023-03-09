"""SimpleTempSensorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from enums import MakeModelMap
from enums import Unit, UnitMap
from enums import TelemetryNameMap


class SimpleTempSensorCac(ComponentAttributeClass):
    by_id: Dict[str, "SimpleTempSensorCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        exponent: int,
        typical_response_time_ms: int,
        temp_unit_gt_enum_symbol: str,
        make_model_gt_enum_symbol: str,
        telemetry_name_gt_enum_symbol: str,
        display_name: Optional[str] = None,
        comms_method: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            component_attribute_class_id=component_attribute_class_id, display_name=display_name
        )

        self.exponent = exponent
        self.comms_method = comms_method
        self.typical_response_time_ms = typical_response_time_ms
        self.telemetry_name = TelemetryNameMap.gt_to_local(telemetry_name_gt_enum_symbol)
        self.temp_unit = UnitMap.gt_to_local(temp_unit_gt_enum_symbol)
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)

        SimpleTempSensorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self
        if self.temp_unit not in [Unit.Celcius, Unit.Fahrenheit, Unit.Unitless]:
            raise Exception("TempSensorCac units must be Fahrenheit, Celsius or Unitless")

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
