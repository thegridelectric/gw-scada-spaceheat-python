"""Makes gt.temp.sensor.cac.100 type"""
# length of GtBooleanActuatorComponent100: 18
from typing import Dict, Optional
from data_classes.cacs.temp_sensor_cac import TempSensorCac

from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac_100 import GtTempSensorCac100
from schema.errors import MpSchemaError
from schema.enums.make_model.make_model_map import MakeModel, MakeModelMap


class GtTempSensorCac_Maker():

    def __init__(self,
                 component_attribute_class_id: str,
                 make_model: MakeModel,
                 display_name: Optional[str],
                 temp_unit: Optional[str],
                 precision_exponent: Optional[int],
                 comms_method: Optional[str]):

        t = GtTempSensorCac100(DisplayName=display_name,
                               TempUnit=temp_unit,
                               MakeModel=make_model,
                               ComponentAttributeClassId=component_attribute_class_id,
                               PrecisionExponent=precision_exponent,
                               CommsMethod=comms_method,
                               )
        t.check_for_errors()
        self.type = t

    @classmethod
    def dict_to_tuple(cls, d: Dict) -> GtTempSensorCac100:
        if "ComponentAttributeClassId" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ComponentAttributeClassId")
        if "SpaceheatMakeModelGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SpaceheatMakeModelGtEnumSymbol")
        d["MakeModel"] = MakeModelMap.gt_to_local(d["SpaceheatMakeModelGtEnumSymbol"])
        if "DisplayName" not in d.keys():
            d["DisplayName"] = None
        if "TempUnit" not in d.keys():
            d["TempUnit"] = None
        if "PrecisionExponent" not in d.keys():
            d["PrecisionExponent"] = None
        if "CommsMethod" not in d.keys():
            d["CommsMethod"] = None

        t = GtTempSensorCac100(DisplayName=d["DisplayName"],
                               TempUnit=d["TempUnit"],
                               ComponentAttributeClassId=d["ComponentAttributeClassId"],
                               PrecisionExponent=d["PrecisionExponent"],
                               CommsMethod=d["CommsMethod"],
                               MakeModel=d["MakeModel"],
                               )
        t.check_for_errors()
        return t

    @classmethod
    def tuple_to_dc(cls, t: GtTempSensorCac100) -> TempSensorCac:
        s = {
            'display_name': t.DisplayName,
            'temp_unit': t.TempUnit,
            'component_attribute_class_id': t.ComponentAttributeClassId,
            'precision_exponent': t.PrecisionExponent,
            'comms_method': t.CommsMethod,
            'make_model_gt_enum_symbol': MakeModelMap.local_to_gt(t.MakeModel), }
        if s['component_attribute_class_id'] in TempSensorCac.by_id.keys():
            dc = TempSensorCac.by_id[s['component_attribute_class_id']]
        else:
            dc = TempSensorCac(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: TempSensorCac) -> GtTempSensorCac100:
        if dc is None:
            return None
        t = GtTempSensorCac100(DisplayName=dc.display_name,
                               TempUnit=dc.temp_unit,
                               MakeModel=dc.make_model,
                               ComponentAttributeClassId=dc.component_attribute_class_id,
                               PrecisionExponent=dc.precision_exponent,
                               CommsMethod=dc.comms_method,
                               )
        t.check_for_errors()
        return t

    @classmethod
    def dict_to_dc(cls, d: Dict) -> TempSensorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))

    @classmethod
    def dc_to_dict(cls, dc: TempSensorCac) -> Dict:
        return cls.dc_to_tuple(dc).asdict()
