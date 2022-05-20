from typing import Optional

from .component import Component
from .actuator_cac import ActuatorCac 
from .errors import DcError, DataClassLoadingError

class ActuatorComponent(Component):
    by_id = {}
    
    base_props = []
    base_props.append('component_id')
    base_props.append('display_name')
    base_props.append('cac_id')
    base_props.append('gpio')

    def __new__(cls, component_id, *args, **kwargs):
        if component_id in Component.by_id.keys():
            if not isinstance(Component.by_id[component_id], cls):
                raise Exception(f"Id already exists, not an actuator!")
            return Component.by_id[component_id]
        instance = super().__new__(cls,component_id=component_id)
        Component.by_id[component_id] = instance
        return instance

    def __init__(self,
                 component_id: Optional[str] = None,
                 display_name: Optional[str] = None,
                 cac_id: Optional[str] = None,
                 gpio: Optional[int] = None):
        super(ActuatorComponent, self).__init__(component_id=component_id,
                            display_name=display_name,
                            cac_id=cac_id)
        self.gpio= gpio

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
        ActuatorComponent.check_uniqueness_of_primary_key(attributes)
        ActuatorComponent.check_existence_of_certain_attributes(attributes)

    @property
    def cac(self) -> ActuatorCac:
        if self.cac_id not in ActuatorCac.by_id.keys():
            raise DataClassLoadingError(f"ActuatorCacId {self.cac_id} not loaded yet")
        return ActuatorCac.by_id[self.cac_id]

    @property
    def make_and_model(self) -> str:
        if self.cac_id not in ActuatorCac.by_id.keys():
            raise DataClassLoadingError(f"ActuatorCacId {self.cac_id} not loaded yet")
        return f'{ActuatorCac.by_id[self.cac_id].make}__{ActuatorCac.by_id[self.cac_id].model}'