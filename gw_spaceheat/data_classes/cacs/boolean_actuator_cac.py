"""BooleanActuatorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from enums import MakeModelMap
from enums import TelemetryName


class BooleanActuatorCac(ComponentAttributeClass):
    by_id: Dict[str, "BooleanActuatorCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model_gt_enum_symbol: str,
        typical_response_time_ms: Optional[int],
        display_name: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            component_attribute_class_id=component_attribute_class_id, display_name=display_name
        )

        self.typical_response_time_ms = typical_response_time_ms
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)
        BooleanActuatorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"

    @property
    def telemetry_name(self):
        return TelemetryName.RelayState
