"""TempSensorComponentBase definition"""

from abc import abstractmethod
from typing import Optional, Dict

from schema.enums.make_model.make_model_map import MakeModel
from schema.gt.gt_temp_sensor_component.gt_temp_sensor_component_100 import GtTempSensorComponent100
from data_classes.component import Component
from data_classes.errors import DcError
from data_classes.cacs.temp_sensor_cac import TempSensorCac


class TempSensorComponentBase(Component):
    _by_id: Dict = {}
    base_props = []
    base_props.append("display_name")
    base_props.append("component_id")
    base_props.append("hw_uid")
    base_props.append("component_attribute_class_id")

    def __init__(self, component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str] = None,
                 hw_uid: Optional[str] = None,
                 ):

        super(TempSensorComponentBase, self).__init__(component_id=component_id,
                                                      display_name=display_name,
                                                      component_attribute_class_id=component_attribute_class_id,
                                                      hw_uid=hw_uid)
        self.hw_uid = hw_uid
        self.component_attribute_class_id = component_attribute_class_id   #
        TempSensorComponentBase._by_id[self.component_id] = self
        Component.by_id[self.component_id] = self

    def update(self, type: GtTempSensorComponent100):
        self._check_immutability_constraints(type=type)

    def _check_immutability_constraints(self, type: GtTempSensorComponent100):
        if self.component_id != type.ComponentId:
            raise DcError(f'component_id must be immutable for {self}. '
                          f'Got {type.ComponentId}')
        if self.hw_uid:
            if self.hw_uid != type.HwUid:
                raise DcError(f'hw_uid must be immutable for {self}. '
                              f'Got {type.HwUid}')
        if self.component_attribute_class_id != type.ComponentAttributeClassId:
            raise DcError(f'component_attribute_class_id must be immutable for {self}. '
                          f'Got {type.ComponentAttributeClassId}')

    @property
    def cac(self) -> TempSensorCac:
        return TempSensorCac.by_id[self.component_attribute_class_id]

    @property
    def make_model(self) -> MakeModel:
        return self.cac.make_model

    @abstractmethod
    def _check_update_axioms(self, type: GtTempSensorComponent100):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError
