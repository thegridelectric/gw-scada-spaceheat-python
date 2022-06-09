"""Makes gt.boolean.actuator.component type"""

from typing import Dict, Optional
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent

from schema.gt.gt_boolean_actuator_component.gt_boolean_actuator_component import GtBooleanActuatorComponent
from schema.errors import MpSchemaError


class GtBooleanActuatorComponent_Maker():
    type_alias = 'gt.boolean.actuator.component.100'

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str],
                 gpio: Optional[int],
                 hw_uid: Optional[str]):

        t = GtBooleanActuatorComponent(DisplayName=display_name,
                                          ComponentId=component_id,
                                          Gpio=gpio,
                                          HwUid=hw_uid,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtBooleanActuatorComponent:
        if "ComponentId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentId")
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "Gpio" not in d.keys():
            d["Gpio"] = None
        if "HwUid" not in d.keys():
            d["HwUid"] = None

        t = GtBooleanActuatorComponent(DisplayName=d["DisplayName"],
                                          ComponentId=d["ComponentId"],
                                          Gpio=d["Gpio"],
                                          HwUid=d["HwUid"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtBooleanActuatorComponent) -> BooleanActuatorComponent:
        s = {
            'display_name': t.DisplayName,
            'component_id': t.ComponentId,
            'gpio': t.Gpio,
            'hw_uid': t.HwUid,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            }
        if s['component_id'] in BooleanActuatorComponent.by_id.keys():
            dc = BooleanActuatorComponent.by_id[s['component_id']]
        else:
            dc = BooleanActuatorComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: BooleanActuatorComponent) -> GtBooleanActuatorComponent:
        if dc is None:
            return None
        t = GtBooleanActuatorComponent(DisplayName=dc.display_name,
                                          ComponentId=dc.component_id,
                                          Gpio=dc.gpio,
                                          HwUid=dc.hw_uid,
                                          ComponentAttributeClassId=dc.component_attribute_class_id,
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> BooleanActuatorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: BooleanActuatorComponent) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
