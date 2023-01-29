"""Makes multipurpose.sensor.component.gt.000 type"""
import json
from typing import Optional
from typing import List
from data_classes.components.multipurpose_sensor_component import MultipurposeSensorComponent
from schema.enums import (
    TelemetryName,
    TelemetryNameMap,
)

from schema.gt.multipurpose_sensor_component_gt.multipurpose_sensor_component_gt import MultipurposeSensorComponentGt
from schema.errors import MpSchemaError


class MultipurposeSensorComponentGt_Maker:
    type_alias = "multi.temp.sensor.component.gt.000"

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 channel_list: List[str],
                 telemetry_name_list: List[TelemetryName],
                 about_node_name_list: List[str],
                 display_name: Optional[str],
                 hw_uid: Optional[str],
                 ):

        gw_tuple = MultipurposeSensorComponentGt(
            ComponentId=component_id,
            ComponentAttributeClassId=component_attribute_class_id,
            ChannelList=channel_list,
            TelemetryNameList=telemetry_name_list,
            AboutNodeNameList=about_node_name_list,
            DisplayName=display_name,
            HwUid=hw_uid,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: MultipurposeSensorComponentGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> MultipurposeSensorComponentGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> MultipurposeSensorComponentGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "ComponentId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentId")
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "TelemetryNameList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameList")
        if "ChannelList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ChannelList")
        telemetry_name_list = []
        for elt in new_d["TelemetryNameList"]:
            telemetry_name_list.append(TelemetryNameMap.gt_to_local(elt))
        new_d["TelemetryNameList"] = telemetry_name_list
        if "AboutNodeNameList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeNameList")
        if "HwUid" not in new_d.keys():
            new_d["HwUid"] = None
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")

        gw_tuple = MultipurposeSensorComponentGt(
            ComponentId=new_d["ComponentId"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            ChannelList=new_d["ChannelList"],
            TelemetryNameList=new_d["TelemetryNameList"],
            AboutNodeNameList=new_d["AboutNodeNameList"],
            HwUid=new_d["HwUid"],
            DisplayName=new_d["DisplayName"],
            TypeAlias=new_d["TypeAlias"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: MultipurposeSensorComponentGt) -> MultipurposeSensorComponent:
        s = {
            "component_id": t.ComponentId,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            "channel_list": t.ChannelList,
            "telemetry_name_list": t.TelemetryNameList,
            "about_node_name_list": t.AboutNodeNameList,
            "hw_uid": t.HwUid,
            "display_name": t.DisplayName,
        }
        if s["component_id"] in MultipurposeSensorComponent.by_id.keys():
            dc = MultipurposeSensorComponent.by_id[s["component_id"]]
        else:
            dc = MultipurposeSensorComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: MultipurposeSensorComponent) -> MultipurposeSensorComponentGt:
        if dc is None:
            return None
        t = MultipurposeSensorComponentGt(
            ComponentId=dc.component_id,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            ChannelList=dc.channel_list,
            TelemetryNameList=dc.telemetry_name_list,
            AboutNodeNameList=dc.about_node_name_list,
            HwUid=dc.hw_uid,
            DisplayName=dc.display_name,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> MultipurposeSensorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: MultipurposeSensorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> MultipurposeSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
