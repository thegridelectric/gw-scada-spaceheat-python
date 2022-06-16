"""Makes gt.temp.sensor.cac type"""

import json
from typing import Dict, Optional
from data_classes.cacs.temp_sensor_cac import TempSensorCac

from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac import GtTempSensorCac
from schema.errors import MpSchemaError
from schema.enums.unit.unit_map import Unit, UnitMap
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtTempSensorCac_Maker():
    type_alias = 'gt.temp.sensor.cac.100'

    def __init__(self,
                 component_attribute_class_id: str,
                 precision_exponent: int,
                 typical_read_time_ms: int,
                 temp_unit: Unit,
                 make_model: MakeModel,
                 display_name: Optional[str],
                 comms_method: Optional[str]):

        tuple = GtTempSensorCac(DisplayName=display_name,
                                          TempUnit=temp_unit,
                                          MakeModel=make_model,
                                          ComponentAttributeClassId=component_attribute_class_id,
                                          PrecisionExponent=precision_exponent,
                                          CommsMethod=comms_method,
                                          TypicalReadTimeMs=typical_read_time_ms,
                                          )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtTempSensorCac) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtTempSensorCac:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtTempSensorCac:
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "PrecisionExponent" not in d.keys():
            raise MpSchemaError(f"dict {d} missing PrecisionExponent")
        if "TypicalReadTimeMs" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TypicalReadTimeMs")
        if "TempUnitGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TempUnitGtEnumSymbol")
        d["TempUnit"] = UnitMap.gt_to_local(d["TempUnitGtEnumSymbol"])
        if "MakeModelGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing MakeModelGtEnumSymbol")
        d["MakeModel"] = MakeModelMap.gt_to_local(d["MakeModelGtEnumSymbol"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "CommsMethod" not in d.keys():
            d["CommsMethod"] = None

        tuple = GtTempSensorCac(DisplayName=d["DisplayName"],
                                          TempUnit=d["TempUnit"],
                                          MakeModel=d["MakeModel"],
                                          ComponentAttributeClassId=d["ComponentAttributeClassId"],
                                          PrecisionExponent=d["PrecisionExponent"],
                                          CommsMethod=d["CommsMethod"],
                                          TypicalReadTimeMs=d["TypicalReadTimeMs"],
                                          )
        tuple.check_for_errors()
        return tuple

    @classmethod
    def tuple_to_dc(cls, t: GtTempSensorCac) -> TempSensorCac:
        s = {
            'display_name': t.DisplayName,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            'precision_exponent': t.PrecisionExponent,
            'comms_method': t.CommsMethod,
            'typical_read_time_ms': t.TypicalReadTimeMs,
            'temp_unit_gt_enum_symbol': UnitMap.local_to_gt(t.TempUnit),'make_model_gt_enum_symbol': MakeModelMap.local_to_gt(t.MakeModel),}
        if s['component_attribute_class_id'] in TempSensorCac.by_id.keys():
            dc = TempSensorCac.by_id[s['component_attribute_class_id']]
        else:
            dc = TempSensorCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: TempSensorCac) -> GtTempSensorCac:
        if dc is None:
            return None
        t = GtTempSensorCac(DisplayName=dc.display_name,
                                            TempUnit=dc.temp_unit,
                                            MakeModel=dc.make_model,
                                            ComponentAttributeClassId=dc.component_attribute_class_id,
                                            PrecisionExponent=dc.precision_exponent,
                                            CommsMethod=dc.comms_method,
                                            TypicalReadTimeMs=dc.typical_read_time_ms,
                                            )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> TempSensorCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: TempSensorCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> TempSensorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
