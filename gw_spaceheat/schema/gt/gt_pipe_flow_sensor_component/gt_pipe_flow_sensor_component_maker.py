"""Makes gt.pipe.flow.sensor.component type"""

from typing import Dict, Optional
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent

from schema.gt.gt_pipe_flow_sensor_component.gt_pipe_flow_sensor_component import GtPipeFlowSensorComponent
from schema.errors import MpSchemaError


class GtPipeFlowSensorComponent_Maker():
    type_alias = 'gt.pipe.flow.sensor.component.100'

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str],
                 hw_uid: Optional[str]):

        t = GtPipeFlowSensorComponent(ComponentId=component_id,
                                          DisplayName=display_name,
                                          HwUid=hw_uid,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtPipeFlowSensorComponent:
        if "ComponentId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentId")
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "HwUid" not in d.keys():
            d["HwUid"] = None

        t = GtPipeFlowSensorComponent(ComponentId=d["ComponentId"],
                                          DisplayName=d["DisplayName"],
                                          HwUid=d["HwUid"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtPipeFlowSensorComponent) -> PipeFlowSensorComponent:
        s = {
            'component_id': t.ComponentId,
            'display_name': t.DisplayName,
            'hw_uid': t.HwUid,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            }
        if s['component_id'] in PipeFlowSensorComponent.by_id.keys():
            dc = PipeFlowSensorComponent.by_id[s['component_id']]
        else:
            dc = PipeFlowSensorComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: PipeFlowSensorComponent) -> GtPipeFlowSensorComponent:
        if dc is None:
            return None
        t = GtPipeFlowSensorComponent(ComponentId=dc.component_id,
                                          DisplayName=dc.display_name,
                                          HwUid=dc.hw_uid,
                                          ComponentAttributeClassId=dc.component_attribute_class_id,
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> PipeFlowSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: PipeFlowSensorComponent) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
