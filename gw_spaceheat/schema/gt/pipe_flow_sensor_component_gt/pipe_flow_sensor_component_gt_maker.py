"""Makes pipe.flow.sensor.component.gt.000 type"""
import json
from typing import Optional
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent

from schema.gt.pipe_flow_sensor_component_gt.pipe_flow_sensor_component_gt import PipeFlowSensorComponentGt
from schema.errors import MpSchemaError


class PipeFlowSensorComponentGt_Maker:
    type_alias = "pipe.flow.sensor.component.gt.000"

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 i2c_address: int,
                 conversion_factor: float,
                 display_name: Optional[str],
                 hw_uid: Optional[str]):

        gw_tuple = PipeFlowSensorComponentGt(
            ComponentId=component_id,
            I2cAddress=i2c_address,
            ConversionFactor=conversion_factor,
            DisplayName=display_name,
            ComponentAttributeClassId=component_attribute_class_id,
            HwUid=hw_uid,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: PipeFlowSensorComponentGt) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> PipeFlowSensorComponentGt:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> PipeFlowSensorComponentGt:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ComponentId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentId")
        if "ConversionFactor" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ConversionFactor")
        if "I2cAddress" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing I2cAddress")
        if "DisplayName" not in new_d.keys():
            new_d["DisplayName"] = None
        if "ComponentAttributeClassId" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ComponentAttributeClassId")
        if "HwUid" not in new_d.keys():
            new_d["HwUid"] = None

        gw_tuple = PipeFlowSensorComponentGt(
            TypeAlias=new_d["TypeAlias"],
            ComponentId=new_d["ComponentId"],
            I2cAddress=new_d["I2cAddress"],
            ConversionFactor=new_d["ConversionFactor"],
            DisplayName=new_d["DisplayName"],
            ComponentAttributeClassId=new_d["ComponentAttributeClassId"],
            HwUid=new_d["HwUid"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple

    @classmethod
    def tuple_to_dc(cls, t: PipeFlowSensorComponentGt) -> PipeFlowSensorComponent:
        s = {
            "component_id": t.ComponentId,
            "display_name": t.DisplayName,
            "i2c_address": t.I2cAddress,
            "conversion_factor": t.ConversionFactor,
            "hw_uid": t.HwUid,
            "component_attribute_class_id": t.ComponentAttributeClassId,
            #
        }
        if s["component_id"] in PipeFlowSensorComponent.by_id.keys():
            dc = PipeFlowSensorComponent.by_id[s["component_id"]]
        else:
            dc = PipeFlowSensorComponent(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: PipeFlowSensorComponent) -> PipeFlowSensorComponentGt:
        if dc is None:
            return None
        t = PipeFlowSensorComponentGt(
            ComponentId=dc.component_id,
            DisplayName=dc.display_name,
            I2cAddress=dc.i2c_address,
            ConversionFactor=dc.conversion_factor,
            HwUid=dc.hw_uid,
            ComponentAttributeClassId=dc.component_attribute_class_id,
            #
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> PipeFlowSensorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: PipeFlowSensorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> PipeFlowSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
