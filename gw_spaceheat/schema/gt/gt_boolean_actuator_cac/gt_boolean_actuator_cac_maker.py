"""Makes gt.boolean.actuator.cac.100 type"""
import json
from typing import Optional
from data_classes.cacs.boolean_actuator_cac import BooleanActuatorCac

from schema.gt.gt_boolean_actuator_cac.gt_boolean_actuator_cac import GtBooleanActuatorCac
from schema.errors import MpSchemaError
from enums import (
    MakeModel,
    MakeModelMap,
)


class GtBooleanActuatorCac_Maker:
    type_alias = "gt.boolean.actuator.cac.100"

    def __init__(self,
                 make_model: MakeModel,
                 component_attribute_class_id: str,
                 typical_response_time_ms: int,
                 display_name: Optional[str]):

        gw_tuple = GtBooleanActuatorCac(
            MakeModel=make_model,
            ComponentAttributeClassId=component_attribute_class_id,
            TypicalResponseTimeMs=typical_response_time_ms,
            DisplayName=display_name,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtBooleanActuatorCac) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtBooleanActuatorCac:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtBooleanActuatorCac:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "MakeModelGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing MakeModelGtEnumSymbol")
        new_d["MakeModel"] = MakeModelMap.gt_to_local(new_d["MakeModelGtEnumSymbol"])
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "TypicalResponseTimeMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypicalResponseTimeMs")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None

        gw_tuple = GtBooleanActuatorCac(
            TypeAlias=new_d["TypeAlias"],
            MakeModel=new_d["MakeModel"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            TypicalResponseTimeMs=new_d["TypicalResponseTimeMs"],
            DisplayName=new_d["DisplayName"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: GtBooleanActuatorCac) -> BooleanActuatorCac:
        s = {
            "component_attribute_class_id": t.ComponentAttributeClassId,
            "typical_response_time_ms": t.TypicalResponseTimeMs,
            "display_name": t.DisplayName,
            "make_model_gt_enum_symbol": MakeModelMap.local_to_gt(t.MakeModel),
            #
        }
        if s["component_attribute_class_id"] in BooleanActuatorCac.by_id.keys():
            dc = BooleanActuatorCac.by_id[s["component_attribute_class_id"]]
        else:
            dc = BooleanActuatorCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: BooleanActuatorCac) -> GtBooleanActuatorCac:
        if dc is None:
            return None
        t = GtBooleanActuatorCac(
            MakeModel=dc.make_model,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            TypicalResponseTimeMs=dc.typical_response_time_ms,
            DisplayName=dc.display_name,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> BooleanActuatorCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: BooleanActuatorCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> BooleanActuatorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
