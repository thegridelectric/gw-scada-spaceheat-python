"""ElectricMeterCac definition"""
from typing import Dict, Optional, List

from data_classes.component_attribute_class import ComponentAttributeClass
from enums import LocalCommInterface, MakeModel, TelemetryName


class ElectricMeterCac(ComponentAttributeClass):
    by_id: Dict[str, "ElectricMeterCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: MakeModel,
        interface: LocalCommInterface,
        poll_period_ms: int,
        default_baud: int,
        display_name: Optional[str] = None,
        telemetry_name_list: List[TelemetryName] = []
    ):
        super(self.__class__, self).__init__(
            component_attribute_class_id=component_attribute_class_id,
            display_name=display_name,
        )
        self.default_baud = default_baud
        self.poll_period_ms = poll_period_ms
        self.interface = interface
        self.make_model = make_model
        self.telemetry_name_list = telemetry_name_list
        ElectricMeterCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self


    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
