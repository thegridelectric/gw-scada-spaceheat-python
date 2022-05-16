from typing import Optional

from data_classes.component import Component
from data_classes.electric_heater_cac import ElectricHeaterCac
from .errors import DataClassLoadingError, DcError

class ElectricHeaterComponent(Component):
    by_id = {}
    
    base_props = []
    base_props.append('component_id')
    base_props.append('display_name')
    base_props.append('cac_id')

    def __new__(cls, component_id, *args, **kwargs):
        if component_id in Component.by_id.keys():
            if not isinstance(Component.by_id[component_id], cls):
                raise Exception(f"Id already exists, not a sensor!")
            return Component.by_id[component_id]
        instance = super().__new__(cls,component_id=component_id)
        Component.by_id[component_id] = instance
        return instance

    def __init__(self,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 cac_id: Optional[str] = None):
        super(ElectricHeaterComponent, self).__init__(component_id=component_id,
                            display_name=display_name,
                            cac_id=cac_id)

    def __repr__(self):
        return f'Component {self.display_name} => Cac {self.cac.display_name}'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_id'] in cls.by_id.keys():
            raise DcError(f"component_id {attributes['component_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not attributes.get('component_id', None):
            raise DcError('component_id must exist')
        if not attributes.get('cac_id', None):
            raise DcError('cac_id must exist')
        if not attributes.get('display_name', None):
            raise DcError('display_name must exist')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        ElectricHeaterComponent.check_uniqueness_of_primary_key(attributes)
        ElectricHeaterComponent.check_existence_of_certain_attributes(attributes)

    @property
    def cac(self) -> ElectricHeaterCac:
        if self.cac_id not in ElectricHeaterCac.by_id.keys():
            raise DataClassLoadingError(f"ElectricHeaterCacId {self.cac_id} not loaded yet")
        return ElectricHeaterCac.by_id[self.cac_id]