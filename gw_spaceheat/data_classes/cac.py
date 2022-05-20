""" SCADA  Cac Class Definition """
import time
import uuid
from typing import Optional
from abc import ABC
from .errors import DcError
from .mixin import StreamlinedSerializerMixin

class Cac(ABC, StreamlinedSerializerMixin):
    by_id = {}

    base_props = []
    base_props.append('cac_id')
    base_props.append('make')
    base_props.append('model')

    def __new__(cls, cac_id, *args, **kwargs):
        try:
            return cls.by_id[cac_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[cac_id] = instance
            return instance

    def __init__(self,
            cac_id: Optional[str] = None,
            make: Optional[str] = None,
            model: Optional[str] = None):
        self.cac_id = cac_id
        self.make = make 
        self.model = model

    @property
    def display_name(self) -> str:
        return f'{self.make}__{self.model} (id {self.cac_id})'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['cac_id'] in cls.by_id.keys():
            raise DcError(f"cac_id {attributes['cac_id']} already in use")


    @classmethod
    def check_initialization_consistency(cls, attributes):
        Cac.check_uniqueness_of_primary_key(attributes)
    
    def check_immutability_for_existing_attributes(self, new_attributes):
        if new_attributes['cac_id'] != self.electric_heater_cac_id:
            raise DcError('cac_id is Immutable')
   
