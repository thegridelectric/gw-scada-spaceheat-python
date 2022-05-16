""" ElectricHeaterCac Class Definition """
from typing import Optional
from .errors import DcError
from .cac import Cac
from .electric_heater_type import ElectricHeaterType
from .electric_heater_type_static import PlatformElectricHeaterType

class ElectricHeaterCac(Cac):
    by_id = {}

    base_props = []
    base_props.append('cac_id')
    base_props.append('electric_heater_type_value')
    
    def __new__(cls, cac_id, *args, **kwargs):
        if cac_id in Cac.by_id.keys():
            if not isinstance(Cac.by_id[cac_id], cls):
                raise Exception(f"Id already exists, not an Electric Heater!")
            return Cac.by_id[cac_id]
        instance = super().__new__(cls,cac_id=cac_id)
        Cac.by_id[cac_id] = instance
        return instance

    def __init__(self,
            cac_id: Optional[str] = None,
            electric_heater_type_value: Optional[str] = None):
        super(ElectricHeaterCac, self).__init__(cac_id=cac_id)
        self.electric_heater_type_value=electric_heater_type_value

    def __repr__(self):
        return f'ElectricHeaterCac ({self.display_name})) {self.cac_id}'

    @property
    def display_name(self) -> str:
        return f'{self.electric_heater_type_value} random co'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['cac_id'] in Cac.by_id.keys():
            raise DcError(f"cac_id {attributes['cac_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not attributes.get('cac_id', None):
            raise DcError('cac_id must exist')
        if not attributes.get('electric_heater_type_value', None):
            raise DcError('electric_heater_type_value')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        ElectricHeaterCac.check_uniqueness_of_primary_key(attributes)
        ElectricHeaterCac.check_existence_of_certain_attributes(attributes)
    
    def check_immutability_for_existing_attributes(self, new_attributes):
        if new_attributes['cac_id'] != self.cac_id:
            raise DcError('cac_id is Immutable')
        if new_attributes['electric_heater_type_value'] != self.electric_heater_type_value:
            raise DcError(f"electric_heater_type_value is Immutable. Not changing {self.display_name}"
                                    f" from {self.electric_heater_type_value} to {new_attributes['electric_heater_type_value']}")
    
    @property
    def electric_heater_type(self) -> ElectricHeaterType:
        if self.electric_heater_type_value not in PlatformElectricHeaterType.keys():
            raise TypeError('electric heater type must belong to static list')
        return PlatformElectricHeaterType[self.electric_heater_type_value]