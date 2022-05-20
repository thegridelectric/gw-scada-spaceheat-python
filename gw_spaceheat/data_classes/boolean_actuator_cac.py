""" ActuatorCac Class Definition """
from typing import Optional
from data_classes.errors import DcError
from data_classes.cac import Cac

class BooleanActuatorCac(Cac):
    by_id = {}

    base_props = []
    base_props.append('cac_id')
    base_props.append('make')
    base_props.append('model')

    
    def __new__(cls, cac_id, *args, **kwargs):
        if cac_id in Cac.by_id.keys():
            if not isinstance(Cac.by_id[cac_id], cls):
                raise Exception(f"Id already exists, not an actuator!")
            return Cac.by_id[cac_id]
        instance = super().__new__(cls,cac_id=cac_id)
        Cac.by_id[cac_id] = instance
        return instance

    def __init__(self,
            cac_id: Optional[str] = None,
            actuator_type_value: Optional[str] = None,
            make: Optional[str] = None,
            model: Optional[str] = None):
        super(ActuatorCac, self).__init__(cac_id=cac_id,
                        make=make,
                        model=model)
        self.actuator_type_value = actuator_type_value
    
    def __repr__(self):
        return f'SensorCac ({self.display_name}) {self.cac_id}'

    @property
    def display_name(self) -> str:
        return f'{self.actuator_type_value} {self.make}__{self.model}'

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['cac_id'] in Cac.by_id.keys():
            raise DcError(f"cac_id {attributes['cac_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not attributes.get('cac_id', None):
            raise DcError('cac_id must exist')
        if not attributes.get('actuator_type_value', None):
            raise DcError('actuator_type_value')

    @classmethod
    def check_initialization_consistency(cls, attributes):
       ActuatorCac.check_uniqueness_of_primary_key(attributes)
       ActuatorCac.check_existence_of_certain_attributes(attributes)
    
    def check_immutability_for_existing_attributes(self, new_attributes):
        if new_attributes['cac_id'] != self.cac_id:
            raise DcError('cac_id is Immutable')
        if new_attributes['actuator_type_value'] != self.actuator_type_value:
            raise DcError(f"actuator_type_value is Immutable. Not changing {self.display_name}"
                                    f" from {self.actuator_type_value} to {new_attributes['actuator_type_value']}")
    
    @property
    def actuator_type(self) -> ActuatorType:
        if self.actuator_type_value not in PlatformActuatorType.keys():
            raise TypeError('electric heater type must belong to static list')
        return PlatformActuatorType[self.actuator_type_value]