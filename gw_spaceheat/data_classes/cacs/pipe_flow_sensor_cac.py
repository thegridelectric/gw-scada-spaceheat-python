"""PipeFlowSensorCac definition"""
from typing import Dict, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.cacs.pipe_flow_sensor_cac_base import PipeFlowSensorCacBase
from schema.gt.gt_pipe_flow_sensor_cac.gt_pipe_flow_sensor_cac import GtPipeFlowSensorCac


class PipeFlowSensorCac(PipeFlowSensorCacBase):
    by_id: Dict[str, "PipeFlowSensorCac"] = {}

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 comms_method: Optional[str] = None,
                 ):
        super(self.__class__, self).__init__(display_name=display_name,
                                             component_attribute_class_id=component_attribute_class_id,
                                             comms_method=comms_method,
                                             make_model_gt_enum_symbol=make_model_gt_enum_symbol,
                                             )
        PipeFlowSensorCac.by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def _check_update_axioms(self, type: GtPipeFlowSensorCac):
        pass

    def __repr__(self):
        return f"{self.make_model.value} {self.display_name}"
