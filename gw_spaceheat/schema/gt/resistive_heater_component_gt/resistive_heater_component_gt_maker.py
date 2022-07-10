"""Makes resistive.heater.component.gt.100 type"""
import json
from typing import Optional
from data_classes.components.resistive_heater_component import ResistiveHeaterComponent

from schema.gt.resistive_heater_component_gt.resistive_heater_component_gt import ResistiveHeaterComponentGt
from schema.errors import MpSchemaError


class ResistiveHeaterComponentGt_Maker:
    type_alias = "resistive.heater.component.gt.100"

    def __init__(self,
                 component_attribute_class_id: str,
                 component_id: str,
                 display_name: Optional[str],
                 tested_max_hot_milli_ohms: Optional[int],
                 hw_uid: Optional[str],
                 tested_max_cold_milli_ohms: Optional[int]):

        gw_tuple = ResistiveHeaterComponentGt(
            DisplayName=display_name,
            TestedMaxHotMilliOhms=tested_max_hot_milli_ohms,
            ComponentAttributeClassId=component_attribute_class_id,
            HwUid=hw_uid,
            ComponentId=component_id,
            TestedMaxColdMilliOhms=tested_max_cold_milli_ohms,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: ResistiveHeaterComponentGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> ResistiveHeaterComponentGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> ResistiveHeaterComponentGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "TestedMaxHotMilliOhms" not in new_d.keys():
            new_d["TestedMaxHotMilliOhms"] = None
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "HwUid" not in new_d.keys():
            new_d["HwUid"] = None
        if "ComponentId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentId")
        if "TestedMaxColdMilliOhms" not in new_d.keys():
            new_d["TestedMaxColdMilliOhms"] = None

        gw_tuple = ResistiveHeaterComponentGt(
            TypeAlias=new_d["TypeAlias"],
            DisplayName=new_d["DisplayName"],
            TestedMaxHotMilliOhms=new_d["TestedMaxHotMilliOhms"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            HwUid=new_d["HwUid"],
            ComponentId=new_d["ComponentId"],
            TestedMaxColdMilliOhms=new_d["TestedMaxColdMilliOhms"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: ResistiveHeaterComponentGt) -> ResistiveHeaterComponent:
        s = {
            "display_name": t.DisplayName,
            "tested_max_hot_milli_ohms": t.TestedMaxHotMilliOhms,
            "hw_uid": t.HwUid,
            "component_id": t.ComponentId,
            "tested_max_cold_milli_ohms": t.TestedMaxColdMilliOhms,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            #
        }
        if s["component_id"] in ResistiveHeaterComponent.by_id.keys():
            dc = ResistiveHeaterComponent.by_id[s["component_id"]]
        else:
            dc = ResistiveHeaterComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ResistiveHeaterComponent) -> ResistiveHeaterComponentGt:
        if dc is None:
            return None
        t = ResistiveHeaterComponentGt(
            DisplayName=dc.display_name,
            TestedMaxHotMilliOhms=dc.tested_max_hot_milli_ohms,
            HwUid=dc.hw_uid,
            ComponentId=dc.component_id,
            TestedMaxColdMilliOhms=dc.tested_max_cold_milli_ohms,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ResistiveHeaterComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ResistiveHeaterComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> ResistiveHeaterComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
