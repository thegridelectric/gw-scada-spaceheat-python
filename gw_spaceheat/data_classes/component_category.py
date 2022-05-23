""" SCADA Component Category Class defintion """

from typing import Optional
from abc import ABC

from data_classes.mixin import StreamlinedSerializerMixin
from data_classes.errors import DcError, DataClassLoadingError
class ComponentCategory(ABC, StreamlinedSerializerMixin):
    by_value = {}
    
    base_props = []
    base_props.append('value')
    base_props.append('description')


    def __new__(cls, value, *args, **kwargs):
        try:
            return cls.value[value]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_value[value] = instance
            return instance

    def __init__(self,
                 value: Optional[str] = None,
                 description: Optional[str] = None):
        self.value = value
        self.description = description

    def __repr__(self):
        return f'Component {self.value}'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['value'] in cls.by_value.keys():
            raise DcError(f"value {attributes['value']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not 'value' in attributes.keys():
            raise DcError('value must exist')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        pass


    def check_immutability_for_existing_attributes(self, new_attributes):
        pass

    def check_update_consistency(self, new_attributes):
        self.check_immutability_for_existing_attributes(new_attributes)

