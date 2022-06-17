"""TempSensorCacBase definition"""

from abc import abstractmethod
from typing import Optional, Dict

from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac import GtTempSensorCac
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.errors import DcError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryNameMap
from schema.enums.unit.unit_map import UnitMap
from schema.enums.make_model.make_model_map import MakeModelMap


class TempSensorCacBase(ComponentAttributeClass):
    base_props = []
    
    base_props.append("telemetry_name")
    base_props.append("display_name")
    base_props.append("temp_unit")
    base_props.append("make_model")
    base_props.append("component_attribute_class_id")
    base_props.append("exponent")
    base_props.append("comms_method")
    base_props.append("typical_response_time_ms")

    def __init__(self, component_attribute_class_id: str,
                 exponent: int,
                 typical_response_time_ms: int,
                 telemetry_name_gt_enum_symbol: str,
                 temp_unit_gt_enum_symbol: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 comms_method: Optional[str] = None,
                 ):

        super(TempSensorCacBase, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                             display_name=display_name)
        self.exponent = exponent
        self.comms_method = comms_method
        self.typical_response_time_ms = typical_response_time_ms
        self.telemetry_name = TelemetryNameMap.gt_to_local(telemetry_name_gt_enum_symbol)
        self.temp_unit = UnitMap.gt_to_local(temp_unit_gt_enum_symbol)
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)

    def update(self, type: GtTempSensorCac):
        self._check_immutability_constraints(type=type)

    def _check_immutability_constraints(self, type: GtTempSensorCac):
        if self.make_model != type.MakeModel:
            raise DcError(f'make_model must be immutable for {self}. '
                          f'Got {type.MakeModel}')
        if self.component_attribute_class_id != type.ComponentAttributeClassId:
            raise DcError(f'component_attribute_class_id must be immutable for {self}. '
                          f'Got {type.ComponentAttributeClassId}')

    @abstractmethod
    def _check_update_axioms(self, type: GtTempSensorCac):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
