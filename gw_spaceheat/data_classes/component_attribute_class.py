""" SCADA  ComponentAttributeClass Definition  (DERIVED FROM GNR gt.gnr.component.attributelcass.200) """
from typing import Optional
from abc import ABC
from .errors import DcError
from .mixin import StreamlinedSerializerMixin

class ComponentAttributeClass(ABC, StreamlinedSerializerMixin):
    by_id = {}

    base_props = []
    base_props.append('component_attribute_class_id')
    base_props.append('make_model')
    base_props.append('component_type_value')


    def __new__(cls, component_attribute_class_id, *args, **kwargs):
        try:
            return cls.by_id[component_attribute_class_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[component_attribute_class_id] = instance
            return instance

    def __init__(self,
            component_attribute_class_id: Optional[str] = None,
            make_model: Optional[str] = None,
            component_type_value: Optional[str] = None):
        self.component_attribute_class_id = component_attribute_class_id
        self.make_model = make_model
        self.component_type_value = component_type_value

    @property
    def display_name(self) -> str:
        return f'{self.make_model} (id {self.component_attribute_class_id})'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_attribute_class_id'] in cls.by_id.keys():
            raise DcError(f"component_attribute_class_id {attributes['component_attribute_class_id']} already in use")

    @classmethod
    def check_initialization_consistency(cls, attributes):
        ComponentAttributeClass.check_uniqueness_of_primary_key(attributes)
    
    def check_immutability_for_existing_attributes(self, new_attributes):
        if new_attributes['component_attribute_class_id'] != self.component_attribute_class_id:
            raise DcError('component_attribute_class_id is Immutable')
        if new_attributes['make_model'] != self.make_model:
            raise DcError('make_model is Immutable')  
        if new_attributes['component_type_value'] != self.component_type_value:
            raise DcError(f"component_type_value is Immutable! Cannot change from {self.component_type_value} to {new_attributes['component_type_value']}")
