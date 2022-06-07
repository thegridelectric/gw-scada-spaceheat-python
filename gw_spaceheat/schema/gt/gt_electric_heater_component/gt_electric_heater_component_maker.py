"""Makes gt.electric.heater.component.100 type"""
# length of GtBooleanActuatorComponent100: 28
from typing import Dict, Optional
from data_classes.components.electric_heater_component import ElectricHeaterComponent

from schema.gt.gt_electric_heater_component.gt_electric_heater_component_100 import GtElectricHeaterComponent100
from schema.errors import MpSchemaError


class GtElectricHeaterComponent_Maker():

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 hw_uid: Optional[str],
                 display_name: Optional[str]):

        t = GtElectricHeaterComponent100(HwUid=hw_uid,
                                          DisplayName=display_name,
                                          ComponentId=component_id,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtElectricHeaterComponent100:
        if "ComponentId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentId")
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "HwUid" not in d.keys():
            d["HwUid"] = None
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None

        t = GtElectricHeaterComponent100(HwUid=d["HwUid"],
                                          DisplayName=d["DisplayName"],
                                          ComponentId=d["ComponentId"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtElectricHeaterComponent100) -> ElectricHeaterComponent:
        s = {
            'hw_uid': t.HwUid,
            'display_name': t.DisplayName,
            'component_id': t.ComponentId,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            }
        if s['component_id'] in ElectricHeaterComponent.by_id.keys():
            dc = ElectricHeaterComponent.by_id[s['component_id']]
        else:
            dc = ElectricHeaterComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricHeaterComponent) -> GtElectricHeaterComponent100:
        if dc is None:
            return None
        t = GtElectricHeaterComponent100(HwUid=dc.hw_uid,
                                          DisplayName=dc.display_name,
                                          ComponentId=dc.component_id,
                                          ComponentAttributeClassId=dc.component_attribute_class_id,
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> ElectricHeaterComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: ElectricHeaterComponent) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
