"""Makes resistive.heater.cac.gt.100 type"""
import json
from typing import Optional
from data_classes.cacs.resistive_heater_cac import ResistiveHeaterCac

from schema.gt.resistive_heater_cac_gt.resistive_heater_cac_gt import ResistiveHeaterCacGt
from schema.errors import MpSchemaError
from enums import (
    MakeModel,
    MakeModelMap,
)


class ResistiveHeaterCacGt_Maker:
    type_alias = "resistive.heater.cac.gt.100"

    def __init__(self,
                 make_model: MakeModel,
                 rated_voltage_v: int,
                 nameplate_max_power_w: int,
                 component_attribute_class_id: str,
                 display_name: Optional[str]):

        gw_tuple = ResistiveHeaterCacGt(
            MakeModel=make_model,
            RatedVoltageV=rated_voltage_v,
            DisplayName=display_name,
            NameplateMaxPowerW=nameplate_max_power_w,
            ComponentAttributeClassId=component_attribute_class_id,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: ResistiveHeaterCacGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> ResistiveHeaterCacGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> ResistiveHeaterCacGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "MakeModelGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing MakeModelGtEnumSymbol")
        new_d["MakeModel"] = MakeModelMap.gt_to_local(new_d["MakeModelGtEnumSymbol"])
        if "RatedVoltageV" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing RatedVoltageV")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "NameplateMaxPowerW" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing NameplateMaxPowerW")
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")

        gw_tuple = ResistiveHeaterCacGt(
            TypeAlias=new_d["TypeAlias"],
            MakeModel=new_d["MakeModel"],
            RatedVoltageV=new_d["RatedVoltageV"],
            DisplayName=new_d["DisplayName"],
            NameplateMaxPowerW=new_d["NameplateMaxPowerW"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: ResistiveHeaterCacGt) -> ResistiveHeaterCac:
        s = {
            "rated_voltage_v": t.RatedVoltageV,
            "display_name": t.DisplayName,
            "nameplate_max_power_w": t.NameplateMaxPowerW,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            "make_model_gt_enum_symbol": MakeModelMap.local_to_gt(t.MakeModel),
            #
        }
        if s["component_attribute_class_id"] in ResistiveHeaterCac.by_id.keys():
            dc = ResistiveHeaterCac.by_id[s["component_attribute_class_id"]]
        else:
            dc = ResistiveHeaterCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ResistiveHeaterCac) -> ResistiveHeaterCacGt:
        if dc is None:
            return None
        t = ResistiveHeaterCacGt(
            MakeModel=dc.make_model,
            RatedVoltageV=dc.rated_voltage_v,
            DisplayName=dc.display_name,
            NameplateMaxPowerW=dc.nameplate_max_power_w,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ResistiveHeaterCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ResistiveHeaterCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> ResistiveHeaterCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
