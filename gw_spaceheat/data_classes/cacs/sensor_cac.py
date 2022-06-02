""" SensorCac Class Definition """
from typing import Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.errors import DcError
from data_classes.sensor_type import SensorType
from data_classes.sensor_type_static import PlatformSensorType


class SensorCac(ComponentAttributeClass):
    by_id = {}

    base_props = []
    base_props.append('component_attribute_class_id')
    base_props.append('make_model')
    base_props.append('display_name')
    base_props.append('sensor_type_value')
    base_props.append('comms_method') 
    
    def __new__(cls, component_attribute_class_id, *args, **kwargs):
        if component_attribute_class_id in ComponentAttributeClass.by_id.keys():
            if not isinstance(ComponentAttributeClass.by_id[component_attribute_class_id], cls):
                raise Exception("Id already exists, not a sensor!")
            return ComponentAttributeClass.by_id[component_attribute_class_id]
        instance = super().__new__(cls, component_attribute_class_id=component_attribute_class_id)
        ComponentAttributeClass.by_id[component_attribute_class_id] = instance
        return instance

    def __init__(self,
             component_attribute_class_id: Optional[str] = None,
             display_name: Optional[str] = None,
             sensor_type_value: Optional[str] = None,
             make_model: Optional[str] = None,
             comms_method: Optional[str] = None):
        super(SensorCac, self).__init__(component_attribute_class_id=component_attribute_class_id,
                         make_model=make_model,
                         display_name=display_name,
                         component_type_value=sensor_type_value)
        self.sensor_type_value = sensor_type_value
        self.comms_method = comms_method

    def __repr__(self):
        val = f'SensorCac {self.make_model}: {self.display_name}'
        if self.comms_method:
            val += f' Comms method: {self.comms_method}'
        return val
    
    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_attribute_class_id'] in ComponentAttributeClass.by_id.keys():
            raise DcError(f"component_attribute_class_id {attributes['component_attribute_class_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if 'component_attribute_class_id' not in attributes.keys():
            raise DcError('component_attribute_class_id must exist')
        """if 'make_model' not in attributes.keys():
            raise DcError(f'make_model must exist for {attributes}')"""
        if 'sensor_type_value' not in attributes.keys():
            raise DcError(f'sensor_type_value must exist for {attributes}')
        """if 'comms_method' not in attributes.keys():
            raise DcError(f"comms_method must exist for {attributes}")"""

    @classmethod
    def check_initialization_consistency(cls, attributes):
        SensorCac.check_uniqueness_of_primary_key(attributes)
        SensorCac.check_existence_of_certain_attributes(attributes)
    
    @property
    def sensor_type(self) -> SensorType:
        if self.sensor_type_value not in PlatformSensorType.keys():
            raise TypeError('electric heater type must belong to static list')
        return PlatformSensorType[self.sensor_type_value]