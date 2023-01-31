"""MutlipurposeSensorComponent definition"""
from typing import Dict, Optional, List

from data_classes.cacs.multipurpose_sensor_cac import MultipurposeSensorCac
from data_classes.component import Component
from schema.enums.make_model.make_model_map import MakeModel
from schema.enums import TelemetryName

class MultipurposeSensorComponent(Component):
    by_id: Dict[str, "MultipurposeSensorComponent"] = {}

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        channel_list: List[int],
        telemetry_name_list: List[TelemetryName],
        about_node_name_list: List[str],
        sample_period_s_list: List[int],
        display_name: Optional[str] = None,
        hw_uid: Optional[str] = None,

    ):
        super(self.__class__, self).__init__(
            display_name=display_name,
            component_id=component_id,
            hw_uid=hw_uid,
            component_attribute_class_id=component_attribute_class_id,
        )
        self.channel_list = channel_list
        self.telemetry_name_list = telemetry_name_list
        self.about_node_name_list = about_node_name_list
        self.sample_period_s_list = sample_period_s_list
        MultipurposeSensorComponent.by_id[self.component_id] = self
        Component.by_id[self.component_id] = self


    @property
    def cac(self) -> MultipurposeSensorCac:
        return MultipurposeSensorCac.by_id[self.component_attribute_class_id]

    @property
    def make_model(self) -> MakeModel:
        return self.cac.make_model

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
