"""Makes gt.pipe.flow.sensor.cac type"""

import json
from typing import Dict, Optional
from data_classes.cacs.pipe_flow_sensor_cac import PipeFlowSensorCac

from schema.gt.gt_pipe_flow_sensor_cac.gt_pipe_flow_sensor_cac import GtPipeFlowSensorCac
from schema.errors import MpSchemaError
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtPipeFlowSensorCac_Maker():
    type_alias = 'gt.pipe.flow.sensor.cac.100'

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: MakeModel,
                 display_name: Optional[str],
                 comms_method: Optional[str]):

        tuple = GtPipeFlowSensorCac(DisplayName=display_name,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          CommsMethod=comms_method,
                                          MakeModel=make_model,
                                          )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtPipeFlowSensorCac) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtPipeFlowSensorCac:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtPipeFlowSensorCac:
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "SpaceheatMakeModelGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SpaceheatMakeModelGtEnumSymbol")
        d["MakeModel"] = MakeModelMap.gt_to_local(d["SpaceheatMakeModelGtEnumSymbol"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "CommsMethod" not in d.keys():
            d["CommsMethod"] = None

        tuple = GtPipeFlowSensorCac(DisplayName=d["DisplayName"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          CommsMethod=d["CommsMethod"],
                                          MakeModel=d["MakeModel"],
                                          )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtPipeFlowSensorCac) -> PipeFlowSensorCac:
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
    def dc_to_tuple(cls, dc: PipeFlowSensorCac) -> GtPipeFlowSensorCac:
        if dc is None:
            return None
        t = GtPipeFlowSensorCac(DisplayName=dc.display_name,
                                            ComponentAttributeClassId=dc.component_attribute_class_id,
                                            CommsMethod=dc.comms_method,
                                            MakeModel=dc.make_model,
                                            )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> PipeFlowSensorCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: PipeFlowSensorCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> PipeFlowSensorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
