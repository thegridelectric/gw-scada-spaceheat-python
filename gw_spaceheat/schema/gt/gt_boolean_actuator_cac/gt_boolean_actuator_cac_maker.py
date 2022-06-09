"""Makes gt.boolean.actuator.cac type"""

from typing import Dict, Optional
from data_classes.cacs.boolean_actuator_cac import BooleanActuatorCac

from schema.gt.gt_boolean_actuator_cac.gt_boolean_actuator_cac import GtBooleanActuatorCac
from schema.errors import MpSchemaError
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtBooleanActuatorCac_Maker():
    type_alias = 'gt.boolean.actuator.cac.100'

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: MakeModel,
                 display_name: Optional[str]):

        t = GtBooleanActuatorCac(MakeModel=make_model,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          DisplayName=display_name,
                                          )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtBooleanActuatorCac:
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "SpaceheatMakeModelGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SpaceheatMakeModelGtEnumSymbol")
        d["MakeModel"] = MakeModelMap.gt_to_local(d["SpaceheatMakeModelGtEnumSymbol"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None

        t = GtBooleanActuatorCac(ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          DisplayName=d["DisplayName"],
                                          MakeModel=d["MakeModel"],
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtBooleanActuatorCac) -> BooleanActuatorCac:
        s = {
            'component_attribute_class_id': t.ComponentAttributeClassId,
            'display_name': t.DisplayName,
            'make_model_gt_enum_symbol': MakeModelMap.local_to_gt(t.MakeModel),}
        if s['component_attribute_class_id'] in BooleanActuatorCac.by_id.keys():
            dc = BooleanActuatorCac.by_id[s['component_attribute_class_id']]
        else:
            dc = BooleanActuatorCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: BooleanActuatorCac) -> GtBooleanActuatorCac:
        if dc is None:
            return None
        t = GtBooleanActuatorCac(MakeModel=dc.make_model,
                                          ComponentAttributeClassId=dc.component_attribute_class_id,
                                          DisplayName=dc.display_name,
                                          )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> BooleanActuatorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: BooleanActuatorCac) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
    
