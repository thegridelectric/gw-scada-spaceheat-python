from typing import Optional

from data_classes.component import Component
from data_classes.boolean_actuator_cac import BooleanActuatorCac
from data_classes.errors import DcError, DataClassLoadingError

class BooleanActuatorComponent(Component):
    by_id = {}
    
    base_props = []
    base_props.append('component_id')
    base_props.append('display_name')
    base_props.append('component_attribute_class_id')
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
                 component_attribute_class_id: Optional[str] = None,
                 gpio: Optional[int] = None):
        super(BooleanActuatorComponent, self).__init__(component_id=component_id,
                            display_name=display_name,
                            component_attribute_class_id=component_attribute_class_id)
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
        if not attributes.get('component_attribute_class_id', None):
            raise DcError('component_attribute_class_id must exist')
        if not attributes.get('display_name', None):
            raise DcError('display_name must exist')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        BooleanActuatorComponent.check_uniqueness_of_primary_key(attributes)
        BooleanActuatorComponent.check_existence_of_certain_attributes(attributes)

    @property
    def cac(self) -> BooleanActuatorCac:
        if self.component_attribute_class_id not in BooleanActuatorCac.by_id.keys():
            raise DataClassLoadingError(f"BooleanActuatorCacId {self.component_attribute_class_id} not loaded yet")
        return BooleanActuatorCac.by_id[self.component_attribute_class_id]

    @property
    def make_model(self) -> str:
        if self.component_attribute_class_id not in BooleanActuatorCac.by_id.keys():
            raise DataClassLoadingError(f"BooleanActuatorCacId {self.component_attribute_class_id} not loaded yet")
        return f'{BooleanActuatorCac.by_id[self.component_attribute_class_id].make_model}'