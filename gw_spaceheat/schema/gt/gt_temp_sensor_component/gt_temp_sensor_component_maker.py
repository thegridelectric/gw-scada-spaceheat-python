"""Makes gt.temp.sensor.component.100 type"""
# length of GtBooleanActuatorComponent100: 24
from typing import Dict, Optional
from data_classes.components.temp_sensor_component import TempSensorComponent

from schema.gt.gt_temp_sensor_component.gt_temp_sensor_component_100 import GtTempSensorComponent100
from schema.errors import MpSchemaError


class GtTempSensorComponent_Maker():

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str],
                 hw_uid: Optional[str]):

        t = GtTempSensorComponent100(DisplayName=display_name,
                                          ComponentId=component_id,
                                          HwUid=hw_uid,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtTempSensorComponent100:
        if "ComponentId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentId")
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "HwUid" not in d.keys():
            d["HwUid"] = None

        t = GtTempSensorComponent100(DisplayName=d["DisplayName"],
                                          ComponentId=d["ComponentId"],
                                          HwUid=d["HwUid"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtTempSensorComponent100) -> TempSensorComponent:
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
    def dc_to_tuple(cls, dc: TempSensorComponent) -> GtTempSensorComponent100:
        if dc is None:
            return None
        t = GtTempSensorComponent100(DisplayName=dc.display_name,
                                          ComponentId=dc.component_id,
                                          HwUid=dc.hw_uid,
                                          ComponentAttributeClassId=dc.component_attribute_class_id,
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> TempSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: TempSensorComponent) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
