"""Makes gt.boolean.actuator.component type"""

import json
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

        tuple = GtBooleanActuatorComponent(DisplayName=display_name,
                                          ComponentId=component_id,
                                          Gpio=gpio,
                                          HwUid=hw_uid,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          )
        tuple.check_for_errors()
        self.tuple: GtBooleanActuatorComponent = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtBooleanActuatorComponent) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtBooleanActuatorComponent:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtBooleanActuatorComponent:
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

        tuple = GtBooleanActuatorComponent(DisplayName=d["DisplayName"],
                                          ComponentId=d["ComponentId"],
                                          Gpio=d["Gpio"],
                                          HwUid=d["HwUid"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          )
        tuple.check_for_errors()
        return tuple

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
    def type_to_dc(cls, t: str) -> BooleanActuatorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: BooleanActuatorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> BooleanActuatorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
