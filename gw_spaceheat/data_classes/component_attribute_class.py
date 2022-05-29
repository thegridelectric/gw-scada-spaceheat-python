""" SCADA  ComponentAttributeClass Definition  (DERIVED FROM GNR gt.gnr.component.attributelcass.200) """
from typing import Optional
from abc import ABC
from data_classes.errors import DcError
from data_classes.mixin import StreamlinedSerializerMixin

class ComponentAttributeClass(ABC, StreamlinedSerializerMixin):
    by_id = {}

    base_props = []
    base_props.append('component_attribute_class_id')
    base_props.append('make_model')
    base_props.append('component_type_value')
    base_props.append('display_name')


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
            component_type_value: Optional[str] = None,
            display_name: Optional[str] = None):
        self.component_attribute_class_id = component_attribute_class_id
        self.make_model = make_model
        self.component_type_value = component_type_value
        self.display_name = display_name

    def __repr__(self):
        return f'MakeModel {self.make_model}: {self.display_name}'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_attribute_class_id'] in cls.by_id.keys():
            raise DcError(f"component_attribute_class_id {attributes['component_attribute_class_id']} already in use")

    @classmethod
    def check_initialization_consistency(cls, attributes):
        ComponentAttributeClass.check_uniqueness_of_primary_key(attributes)
