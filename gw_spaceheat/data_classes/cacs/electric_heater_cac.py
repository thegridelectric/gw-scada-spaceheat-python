""" ElectricHeaterCac Class Definition """
from typing import Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.electric_heater_type import ElectricHeaterType
from data_classes.electric_heater_type_static import PlatformElectricHeaterType
from data_classes.errors import DcError


class ElectricHeaterCac(ComponentAttributeClass):
    by_id = {}

    base_props = []
    base_props.append('component_attribute_class_id')
    base_props.append('make_model')
    base_props.append('display_name')
    base_props.append('electric_heater_type_value')
    
    def __new__(cls, component_attribute_class_id, *args, **kwargs):
        if component_attribute_class_id in ComponentAttributeClass.by_id.keys():
            if not isinstance(ComponentAttributeClass.by_id[component_attribute_class_id], cls):
                raise Exception(f"Id already exists, not an Electric Heater!")
            return ComponentAttributeClass.by_id[component_attribute_class_id]
        instance = super().__new__(cls,component_attribute_class_id=component_attribute_class_id)
        ComponentAttributeClass.by_id[component_attribute_class_id] = instance
        return instance

    def __init__(self,
            component_attribute_class_id: Optional[str] = None,
            electric_heater_type_value: Optional[str] = None, 
            make_model: Optional[str] = None,
            display_name: Optional[str] = None):
        super(ElectricHeaterCac, self).__init__(component_attribute_class_id=component_attribute_class_id,
                        make_model=make_model,
                        display_name=display_name,
                        component_type_value=electric_heater_type_value)
        self.electric_heater_type_value=electric_heater_type_value

    def __repr__(self):
        return f'ElectricHeaterCac ({self.display_name})) {self.component_attribute_class_id}'


    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_attribute_class_id'] in ComponentAttributeClass.by_id.keys():
            raise DcError(f"component_attribute_class_id {attributes['component_attribute_class_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not attributes.get('component_attribute_class_id', None):
            raise DcError('component_attribute_class_id must exist')
        if not attributes.get('electric_heater_type_value', None):
            raise DcError('electric_heater_type_value')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        ElectricHeaterCac.check_uniqueness_of_primary_key(attributes)
        ElectricHeaterCac.check_existence_of_certain_attributes(attributes)
    
    @property
    def electric_heater_type(self) -> ElectricHeaterType:
        if self.electric_heater_type_value not in PlatformElectricHeaterType.keys():
            raise TypeError('electric heater type must belong to static list')
        return PlatformElectricHeaterType[self.electric_heater_type_value]