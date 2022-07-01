"""Makes gt.pipe.flow.sensor.cac.100 type"""

import json
from typing import Optional

from data_classes.cacs.pipe_flow_sensor_cac import PipeFlowSensorCac
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap
from schema.errors import MpSchemaError
from schema.gt.gt_pipe_flow_sensor_cac.gt_pipe_flow_sensor_cac import GtPipeFlowSensorCac


class GtPipeFlowSensorCac_Maker:
    type_alias = "gt.pipe.flow.sensor.cac.100"

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: MakeModel,
        display_name: Optional[str],
        comms_method: Optional[str],
    ):

        tuple = GtPipeFlowSensorCac(
            DisplayName=display_name,
            ComponentAttributeClassId=component_attribute_class_id,
            CommsMethod=comms_method,
            MakeModel=make_model,
        )
        tuple.check_for_errors()
        self.tuple: GtPipeFlowSensorCac = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtPipeFlowSensorCac) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtPipeFlowSensorCac:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtPipeFlowSensorCac:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]

        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "MakeModelGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing MakeModelGtEnumSymbol")
        new_d["MakeModel"] = MakeModelMap.gt_to_local(new_d["MakeModelGtEnumSymbol"])
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "CommsMethod" not in new_d.keys():
            new_d["CommsMethod"] = None

        tuple = GtPipeFlowSensorCac(
            DisplayName=new_d["DisplayName"],
            TypeAlias=new_d["TypeAlias"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            CommsMethod=new_d["CommsMethod"],
            MakeModel=new_d["MakeModel"],
        )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtPipeFlowSensorCac) -> PipeFlowSensorCac:
        s = {
            "display_name": t.DisplayName,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            "comms_method": t.CommsMethod,
            "make_model_gt_enum_symbol": MakeModelMap.local_to_gt(t.MakeModel),
        }
        if s["component_attribute_class_id"] in PipeFlowSensorCac.by_id.keys():
            dc = PipeFlowSensorCac.by_id[s["component_attribute_class_id"]]
        else:
            dc = PipeFlowSensorCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: PipeFlowSensorCac) -> GtPipeFlowSensorCac:
        if dc is None:
            return None
        t = GtPipeFlowSensorCac(
            DisplayName=dc.display_name,
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
