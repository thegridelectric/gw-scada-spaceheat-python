"""PipeFlowSensorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from enums import MakeModel


class PipeFlowSensorCac(ComponentAttributeClass):
    by_id: Dict[str, "PipeFlowSensorCac"] = {}

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: MakeModel,
        display_name: Optional[str] = None,
        comms_method: Optional[str] = None,
    ):
        super(self.__class__, self).__init__(
            component_attribute_class_id=component_attribute_class_id,
            display_name=display_name,
        )

        self.comms_method = comms_method
        self.make_model = make_model

        PipeFlowSensorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
