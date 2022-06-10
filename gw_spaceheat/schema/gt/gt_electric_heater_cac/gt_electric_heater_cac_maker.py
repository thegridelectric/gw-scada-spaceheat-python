"""Makes gt.electric.heater.cac type"""

import json
from typing import Dict, Optional
from data_classes.cacs.electric_heater_cac import ElectricHeaterCac

from schema.gt.gt_electric_heater_cac.gt_electric_heater_cac import GtElectricHeaterCac
from schema.errors import MpSchemaError
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtElectricHeaterCac_Maker():
    type_alias = 'gt.electric.heater.cac.100'

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: MakeModel,
                 display_name: Optional[str]):

        tuple = GtElectricHeaterCac(ComponentAttributeClassId=component_attribute_class_id,
                                          MakeModel=make_model,
                                          DisplayName=display_name,
                                          )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtElectricHeaterCac) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtElectricHeaterCac:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtElectricHeaterCac:
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "SpaceheatMakeModelGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SpaceheatMakeModelGtEnumSymbol")
        d["MakeModel"] = MakeModelMap.gt_to_local(d["SpaceheatMakeModelGtEnumSymbol"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None

        tuple = GtElectricHeaterCac(ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          MakeModel=d["MakeModel"],
                                          DisplayName=d["DisplayName"],
                                          )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtElectricHeaterCac) -> ElectricHeaterCac:
        s = {
            'component_attribute_class_id': t.ComponentAttributeClassId,
            'display_name': t.DisplayName,
            'make_model_gt_enum_symbol': MakeModelMap.local_to_gt(t.MakeModel),}
        if s['component_attribute_class_id'] in ElectricHeaterCac.by_id.keys():
            dc = ElectricHeaterCac.by_id[s['component_attribute_class_id']]
        else:
            dc = ElectricHeaterCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricHeaterCac) -> GtElectricHeaterCac:
        if dc is None:
            return None
        t = GtElectricHeaterCac(ComponentAttributeClassId=dc.component_attribute_class_id,
                                            MakeModel=dc.make_model,
                                            DisplayName=dc.display_name,
                                            )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ElectricHeaterCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ElectricHeaterCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> ElectricHeaterCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
