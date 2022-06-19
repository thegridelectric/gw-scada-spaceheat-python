"""Makes gt.temp.sensor.component type"""

import json
from typing import Dict, Optional
from data_classes.components.temp_sensor_component import TempSensorComponent

from schema.gt.gt_temp_sensor_component.gt_temp_sensor_component import GtTempSensorComponent
from schema.errors import MpSchemaError


class GtTempSensorComponent_Maker():
    type_alias = 'gt.temp.sensor.component.100'

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str],
                 hw_uid: Optional[str]):

        tuple = GtTempSensorComponent(DisplayName=display_name,
                                          ComponentId=component_id,
                                          HwUid=hw_uid,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          )
        tuple.check_for_errors()
        self.tuple: GtTempSensorComponent = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtTempSensorComponent) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtTempSensorComponent:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtTempSensorComponent:
        if "ComponentId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentId")
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "HwUid" not in d.keys():
            d["HwUid"] = None

        tuple = GtTempSensorComponent(DisplayName=d["DisplayName"],
                                          ComponentId=d["ComponentId"],
                                          HwUid=d["HwUid"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtTempSensorComponent) -> TempSensorComponent:
        s = {
            'display_name': t.DisplayName,
            'component_id': t.ComponentId,
            'hw_uid': t.HwUid,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            }
        if s['component_id'] in TempSensorComponent.by_id.keys():
            dc = TempSensorComponent.by_id[s['component_id']]
        else:
            dc = TempSensorComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: TempSensorComponent) -> GtTempSensorComponent:
        if dc is None:
            return None
        t = GtTempSensorComponent(DisplayName=dc.display_name,
                                            ComponentId=dc.component_id,
                                            HwUid=dc.hw_uid,
                                            ComponentAttributeClassId=dc.component_attribute_class_id,
                                            )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> TempSensorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: TempSensorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> TempSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
