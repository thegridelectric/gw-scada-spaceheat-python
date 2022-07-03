"""Makes gt.electric.heater.cac.100 type"""
import json
from typing import Optional
from data_classes.cacs.electric_heater_cac import ElectricHeaterCac

from schema.gt.gt_electric_heater_cac.gt_electric_heater_cac import GtElectricHeaterCac
from schema.errors import MpSchemaError
from schema.enums.make_model.make_model_map import (
    MakeModel,
    MakeModelMap,
)


class GtElectricHeaterCac_Maker:
    type_alias = "gt.electric.heater.cac.100"

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: MakeModel,
                 display_name: Optional[str]):

        gw_tuple = GtElectricHeaterCac(
            ComponentAttributeClassId=component_attribute_class_id,
            MakeModel=make_model,
            DisplayName=display_name,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtElectricHeaterCac) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtElectricHeaterCac:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtElectricHeaterCac:
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

        gw_tuple = GtElectricHeaterCac(
            TypeAlias=new_d["TypeAlias"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            MakeModel=new_d["MakeModel"],
            DisplayName=new_d["DisplayName"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: GtElectricHeaterCac) -> ElectricHeaterCac:
        s = {
            "component_attribute_class_id": t.ComponentAttributeClassId,
            "display_name": t.DisplayName,
            "make_model_gt_enum_symbol": MakeModelMap.local_to_gt(t.MakeModel),
            #
        }
        if s["component_attribute_class_id"] in ElectricHeaterCac.by_id.keys():
            dc = ElectricHeaterCac.by_id[s["component_attribute_class_id"]]
        else:
            dc = ElectricHeaterCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricHeaterCac) -> GtElectricHeaterCac:
        if dc is None:
            return None
        t = GtElectricHeaterCac(
            ComponentAttributeClassId=dc.component_attribute_class_id,
            MakeModel=dc.make_model,
            DisplayName=dc.display_name,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ElectricHeaterCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ElectricHeaterCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> ElectricHeaterCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
