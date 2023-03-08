"""Makes pipe.flow.sensor.cac.gt.000 type"""
import json
from typing import Optional
from data_classes.cacs.pipe_flow_sensor_cac import PipeFlowSensorCac

from schema.gt.pipe_flow_sensor_cac_gt.pipe_flow_sensor_cac_gt import PipeFlowSensorCacGt
from schema.errors import MpSchemaError
from enums import (
    MakeModel,
    MakeModelMap,
)


class PipeFlowSensorCacGt_Maker:
    type_alias = "pipe.flow.sensor.cac.gt.000"

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: MakeModel,
                 display_name: Optional[str],
                 comms_method: Optional[str]):

        gw_tuple = PipeFlowSensorCacGt(
            DisplayName=display_name,
            ComponentAttributeClassId=component_attribute_class_id,
            CommsMethod=comms_method,
            MakeModel=make_model,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: PipeFlowSensorCacGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> PipeFlowSensorCacGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> PipeFlowSensorCacGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "CommsMethod" not in new_d.keys():
            new_d["CommsMethod"] = None
        if "MakeModelGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing MakeModelGtEnumSymbol")
        new_d["MakeModel"] = MakeModelMap.gt_to_local(new_d["MakeModelGtEnumSymbol"])

        gw_tuple = PipeFlowSensorCacGt(
            TypeAlias=new_d["TypeAlias"],
            DisplayName=new_d["DisplayName"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            CommsMethod=new_d["CommsMethod"],
            MakeModel=new_d["MakeModel"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: PipeFlowSensorCacGt) -> PipeFlowSensorCac:
        s = {
            "display_name": t.DisplayName,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            "comms_method": t.CommsMethod,
            "make_model_gt_enum_symbol": MakeModelMap.local_to_gt(t.MakeModel),
            #
        }
        if s["component_attribute_class_id"] in PipeFlowSensorCac.by_id.keys():
            dc = PipeFlowSensorCac.by_id[s["component_attribute_class_id"]]
        else:
            dc = PipeFlowSensorCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: PipeFlowSensorCac) -> PipeFlowSensorCacGt:
        if dc is None:
            return None
        t = PipeFlowSensorCacGt(
            DisplayName=dc.display_name,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            CommsMethod=dc.comms_method,
            MakeModel=dc.make_model,
            #
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
