"""ElectricMeterCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from schema.enums.local_comm_interface.local_comm_interface_map import LocalCommInterfaceMap
from schema.enums.make_model.make_model_map import MakeModelMap, MakeModel
from schema.enums.telemetry_name.spaceheat_telemetry_name_100 import TelemetryName


class ElectricMeterCac(ComponentAttributeClass):
    by_id: Dict[str, "ElectricMeterCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model_gt_enum_symbol: str,
        local_comm_interface_gt_enum_symbol: str,
        update_period_ms: int,
        default_baud: int,
        display_name: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            component_attribute_class_id=component_attribute_class_id, display_name=display_name
        )
        self.default_baud = default_baud
        self.update_period_ms = update_period_ms
        self.local_comm_interface = LocalCommInterfaceMap.gt_to_local(
            local_comm_interface_gt_enum_symbol
        )
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)

        ElectricMeterCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def telemetry_name_list(self):
        if self.make_model == MakeModel.GRIDWORKS__SIMPM1:
            return [TelemetryName.POWER_W, TelemetryName.CURRENT_RMS_MICRO_AMPS]
        elif self.make_model == MakeModel.OPENENERGY__EMONPI:
            return [TelemetryName.POWER_W]
        elif self.make_model == MakeModel.SCHNEIDERELECTRIC__IEM3455:
            return [TelemetryName.POWER_W, TelemetryName.CURRENT_RMS_MICRO_AMPS]
        else:
            return [TelemetryName.POWER_W]

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
