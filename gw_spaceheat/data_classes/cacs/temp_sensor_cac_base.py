"""TempSensorCacBase definition"""

from abc import abstractmethod
from typing import Optional, Dict

from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac_100 import GtTempSensorCac100
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.errors import DcError
from schema.enums.make_model.make_model_map import MakeModelMap


class TempSensorCacBase(ComponentAttributeClass):
    _by_id: Dict = {}
    base_props = []
    
    base_props.append("display_name")
    base_props.append("temp_unit")
    base_props.append("make_model")
    base_props.append("component_attribute_class_id")
    base_props.append("precision_exponent")
    base_props.append("comms_method")

    def __init__(self, component_attribute_class_id: str,
                 make_model_gt_enum_symbol: str,
                 display_name: Optional[str] = None,
                 temp_unit: Optional[str] = None,
                 precision_exponent: Optional[int] = None,
                 comms_method: Optional[str] = None,
                 ):

        super(TempSensorCacBase, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                             display_name=display_name)
        self.temp_unit = temp_unit
        self.precision_exponent = precision_exponent
        self.comms_method = comms_method
        self.make_model = MakeModelMap.gt_to_local(make_model_gt_enum_symbol)   #
        TempSensorCacBase._by_id[self.component_attribute_class_id] = self
        ComponentAttributeClass.by_id[self.component_attribute_class_id] = self

    def update(self, type: GtTempSensorCac100):
        self._check_immutability_constraints(type=type)

    def _check_immutability_constraints(self, type: GtTempSensorCac100):
        if self.make_model != type.MakeModel:
            raise DcError(f'make_model must be immutable for {self}. '
                          f'Got {type.MakeModel}')
        if self.component_attribute_class_id != type.ComponentAttributeClassId:
            raise DcError(f'component_attribute_class_id must be immutable for {self}. '
                          f'Got {type.ComponentAttributeClassId}')

    @abstractmethod
    def _check_update_axioms(self, type: GtTempSensorCac100):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
