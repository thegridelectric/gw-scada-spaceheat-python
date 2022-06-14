"""PipeFlowSensorComponent definition"""
from typing import Dict, Optional

from data_classes.component import Component
from data_classes.components.pipe_flow_sensor_component_base import PipeFlowSensorComponentBase
from schema.gt.gt_pipe_flow_sensor_component.gt_pipe_flow_sensor_component import GtPipeFlowSensorComponent


class PipeFlowSensorComponent(PipeFlowSensorComponentBase):
    by_id: Dict[str, "PipeFlowSensorComponent"] =  {}

    def __init__(self, component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str] = None,
                 hw_uid: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(component_id=component_id,
                                             display_name=display_name,
                                             hw_uid=hw_uid,
                                             component_attribute_class_id=component_attribute_class_id,
                                             )
        PipeFlowSensorComponent.by_id[self.component_id] = self
        Component.by_id[self.component_id] = self

    def _check_update_axioms(self, type: GtPipeFlowSensorComponent):
        pass

    def __repr__(self):
        return f"{self.display_name}  ({self.cac.make_model.value})"
