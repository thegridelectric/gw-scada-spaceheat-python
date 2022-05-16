""" SensorCac Class Definition """
from typing import Optional
from abc import ABC
from .errors import DcError
from .cac import Cac
from .sensor_type import SensorType
from .sensor_type_static import PlatformSensorType

class SensorCac(Cac):
    by_id = {}

    base_props = []
    base_props.append('cac_id')
    base_props.append('sensor_type_value')
    
    def __new__(cls, cac_id, *args, **kwargs):
        if cac_id in Cac.by_id.keys():
            if not isinstance(Cac.by_id[cac_id], cls):
                raise Exception(f"Id already exists, not a sensor!")
            return Cac.by_id[cac_id]
        instance = super().__new__(cls,cac_id=cac_id)
        Cac.by_id[cac_id] = instance
        return instance

    def __init__(self,
            cac_id: Optional[str] = None,
            sensor_type_value: Optional[str] = None):
        super(SensorCac, self).__init__(cac_id=cac_id)
        self.sensor_type_value = sensor_type_value

    def __repr__(self):
        return f'SensorCac ({self.display_name})) {self.cac_id}'
    
    @property
    def display_name(self) -> str:
        return f'{self.sensor_type_value} random co'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['cac_id'] in Cac.by_id.keys():
            raise DcError(f"cac_id {attributes['cac_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if 'cac_id' not in attributes.keys():
            raise DcError('cac_id must exist')
        if 'sensor_type_value' not in attributes.keys():
            raise DcError('sensor_type_value')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        SensorCac.check_uniqueness_of_primary_key(attributes)
        SensorCac.check_existence_of_certain_attributes(attributes)
    
    def check_immutability_for_existing_attributes(self, new_attributes):
        if new_attributes['cac_id'] != self.cac_id:
            raise DcError('cac_id is Immutable')
        if new_attributes['sensor_type_value'] != self.sensor_type_value:
            raise DcError(f"sensor_type_value is Immutable. Not changing {self.display_name}"
                                    f" from {self.sensor_type_value} to {new_attributes['sensor_type_value']}")
    
    @property
    def sensor_type(self) -> SensorType:
        if self.sensor_type_value not in PlatformSensorType.keys():
            raise TypeError('electric heater type must belong to static list')
        return PlatformSensorType[self.sensor_type_value]