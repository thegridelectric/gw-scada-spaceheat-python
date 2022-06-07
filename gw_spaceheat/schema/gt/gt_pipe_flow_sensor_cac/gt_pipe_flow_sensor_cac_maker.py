"""Makes gt.pipe.flow.sensor.cac.100 type"""
# length of GtBooleanActuatorComponent100: 22
from typing import Dict, Optional
from data_classes.cacs.pipe_flow_sensor_cac import PipeFlowSensorCac

from schema.gt.gt_pipe_flow_sensor_cac.gt_pipe_flow_sensor_cac_100 import GtPipeFlowSensorCac100
from schema.errors import MpSchemaError
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtPipeFlowSensorCac_Maker():

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: MakeModel,
                 display_name: Optional[str],
                 comms_method: Optional[str]):

        t = GtPipeFlowSensorCac100(DisplayName=display_name,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          CommsMethod=comms_method,
                                          MakeModel=make_model,
                                          )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtPipeFlowSensorCac100:
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "SpaceheatMakeModelGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SpaceheatMakeModelGtEnumSymbol")
        d["MakeModel"] = MakeModelMap.gt_to_local(d["SpaceheatMakeModelGtEnumSymbol"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "CommsMethod" not in d.keys():
            d["CommsMethod"] = None

        t = GtPipeFlowSensorCac100(DisplayName=d["DisplayName"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          CommsMethod=d["CommsMethod"],
                                          MakeModel=d["MakeModel"],
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtPipeFlowSensorCac100) -> PipeFlowSensorCac:
        s = {
            'display_name': t.DisplayName,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            'comms_method': t.CommsMethod,
            'make_model_gt_enum_symbol': MakeModelMap.local_to_gt(t.MakeModel),}
        if s['component_attribute_class_id'] in PipeFlowSensorCac.by_id.keys():
            dc = PipeFlowSensorCac.by_id[s['component_attribute_class_id']]
        else:
            dc = PipeFlowSensorCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: PipeFlowSensorCac) -> GtPipeFlowSensorCac100:
        if dc is None:
            return None
        t = GtPipeFlowSensorCac100(DisplayName=dc.display_name,
                                          ComponentAttributeClassId=dc.component_attribute_class_id,
                                          CommsMethod=dc.comms_method,
                                          MakeModel=dc.make_model,
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> PipeFlowSensorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: PipeFlowSensorCac) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
