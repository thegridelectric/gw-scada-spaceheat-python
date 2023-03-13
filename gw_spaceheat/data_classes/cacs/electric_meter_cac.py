"""ElectricMeterCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from enums import LocalCommInterface, MakeModel, TelemetryName


class ElectricMeterCac(ComponentAttributeClass):
    by_id: Dict[str, "ElectricMeterCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: MakeModel,
        local_comm_interface: LocalCommInterface,
        update_period_ms: int,
        default_baud: int,
        display_name: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            component_attribute_class_id=component_attribute_class_id,
            display_name=display_name,
        )
        self.default_baud = default_baud
        self.update_period_ms = update_period_ms
        self.local_comm_interface = local_comm_interface
        self.make_model = make_model

        ElectricMeterCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def telemetry_name_list(self):
        if self.make_model == MakeModel.GRIDWORKS__SIMPM1:
            return [TelemetryName.PowerW, TelemetryName.CurrentRmsMicroAmps]
        elif self.make_model == MakeModel.OPENENERGY__EMONPI:
            return [TelemetryName.PowerW]
        elif self.make_model == MakeModel.SCHNEIDERELECTRIC__IEM3455:
            return [TelemetryName.PowerW, TelemetryName.CurrentRmsMicroAmps]
        else:
            return [TelemetryName.PowerW]

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
