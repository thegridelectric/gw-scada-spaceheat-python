""" SCADA Component Class Definition """

from typing import Optional
from abc import ABC

from data_classes.mixin import StreamlinedSerializerMixin
from data_classes.errors import DcError, DataClassLoadingError
from data_classes.cac import Cac
class Component(ABC, StreamlinedSerializerMixin):
    by_id = {}
    
    base_props = []
    base_props.append('component_id')
    base_props.append('display_name')
    base_props.append('cac_id')


    def __new__(cls, component_id, *args, **kwargs):
        try:
            return cls.by_id[component_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[component_id] = instance
            return instance

    def __init__(self,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 cac_id: Optional[str] = None):
        self.component_id = component_id
        self.display_name = display_name
        self.cac_id = cac_id

    def __repr__(self):
        return f'Component {self.display_name}'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_id'] in cls.by_id.keys():
            raise DcError(f"component_id {attributes['component_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not 'component_id' in attributes.keys():
            raise DcError('component_id must exist')
        if not 'electric_heater_cac_id' in attributes.keys():
            raise DcError('electric_heater_cac_id must exist')
        if not 'display_name' in attributes.keys():
            raise DcError('display_name must exist')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        Component.check_uniqueness_of_primary_key(attributes)
        Component.check_existence_of_certain_attributes(attributes)


    def check_immutability_for_existing_attributes(self, new_attributes):
        if new_attributes['component_id'] != self.component_id:
            raise DcError('component_id is Immutable')
        if new_attributes['cac_id'] != self.cac_id:
            raise DcError('cac_id is Immutable')

    def check_update_consistency(self, new_attributes):
        self.check_immutability_for_existing_attributes(new_attributes)

    @property
    def cac(self) -> Cac:
        if self.cac_id not in Cac.by_id.keys():
            raise DataClassLoadingError(f"ActuatorCacId {self.cac_id} not loaded yet")
        return Cac.by_id[self.cac_id]
