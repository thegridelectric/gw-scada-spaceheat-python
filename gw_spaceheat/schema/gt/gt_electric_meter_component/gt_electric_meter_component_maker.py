"""Makes gt.electric.meter.component.100 type"""
# length of GtBooleanActuatorComponent100: 27
from typing import Dict, Optional
from data_classes.components.electric_meter_component import ElectricMeterComponent

from schema.gt.gt_electric_meter_component.gt_electric_meter_component_100 import GtElectricMeterComponent100
from schema.errors import MpSchemaError


class GtElectricMeterComponent_Maker():

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str],
                 hw_uid: Optional[str]):

        t = GtElectricMeterComponent100(DisplayName=display_name,
                                          ComponentId=component_id,
                                          HwUid=hw_uid,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtElectricMeterComponent100:
        if "ComponentId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentId")
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "HwUid" not in d.keys():
            d["HwUid"] = None

        t = GtElectricMeterComponent100(DisplayName=d["DisplayName"],
                                          ComponentId=d["ComponentId"],
                                          HwUid=d["HwUid"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtElectricMeterComponent100) -> ElectricMeterComponent:
        s = {
            'display_name': t.DisplayName,
            'component_id': t.ComponentId,
            'hw_uid': t.HwUid,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            }
        if s['component_id'] in ElectricMeterComponent.by_id.keys():
            dc = ElectricMeterComponent.by_id[s['component_id']]
        else:
            dc = ElectricMeterComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricMeterComponent) -> GtElectricMeterComponent100:
        if dc is None:
            return None
        t = GtElectricMeterComponent100(DisplayName=dc.display_name,
                                          ComponentId=dc.component_id,
                                          HwUid=dc.hw_uid,
                                          ComponentAttributeClassId=dc.component_attribute_class_id,
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> ElectricMeterComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: ElectricMeterComponent) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
