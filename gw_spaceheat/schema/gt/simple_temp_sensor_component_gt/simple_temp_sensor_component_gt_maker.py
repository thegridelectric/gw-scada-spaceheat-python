"""Makes simple.temp.sensor.component.gt.000 type"""
import json
from typing import Optional
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent

from schema.gt.simple_temp_sensor_component_gt.simple_temp_sensor_component_gt import SimpleTempSensorComponentGt
from schema.errors import MpSchemaError


class SimpleTempSensorComponentGt_Maker:
    type_alias = "simple.temp.sensor.component.gt.000"

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str],
                 hw_uid: Optional[str],
                 channel: Optional[int],):

        gw_tuple = SimpleTempSensorComponentGt(
            DisplayName=display_name,
            ComponentId=component_id,
            ComponentAttributeClassId=component_attribute_class_id,
            HwUid=hw_uid,
            Channel=channel,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: SimpleTempSensorComponentGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> SimpleTempSensorComponentGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> SimpleTempSensorComponentGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "ComponentId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentId")
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "HwUid" not in new_d.keys():
            new_d["HwUid"] = None
        if "Channel" not in new_d.keys():
            new_d["Channel"] = None

        gw_tuple = SimpleTempSensorComponentGt(
            TypeAlias=new_d["TypeAlias"],
            DisplayName=new_d["DisplayName"],
            ComponentId=new_d["ComponentId"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            HwUid=new_d["HwUid"],
            Channel=new_d["Channel"]
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: SimpleTempSensorComponentGt) -> SimpleTempSensorComponent:
        s = {
            "display_name": t.DisplayName,
            "component_id": t.ComponentId,
            "hw_uid": t.HwUid,
            "channel": t.Channel,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            #
        }
        if s["component_id"] in SimpleTempSensorComponent.by_id.keys():
            dc = SimpleTempSensorComponent.by_id[s["component_id"]]
        else:
            dc = SimpleTempSensorComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: SimpleTempSensorComponent) -> SimpleTempSensorComponentGt:
        if dc is None:
            return None
        t = SimpleTempSensorComponentGt(
            DisplayName=dc.display_name,
            ComponentId=dc.component_id,
            HwUid=dc.hw_uid,
            Channel=dc.channel,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> SimpleTempSensorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: SimpleTempSensorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> SimpleTempSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
