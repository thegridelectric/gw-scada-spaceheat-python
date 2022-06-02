""" ActuatorCac Class Definition """
from typing import Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.errors import DcError


class BooleanActuatorCac(ComponentAttributeClass):
    by_id = {}
    base_props = []
    base_props.append('component_attribute_class_id')
    base_props.append('make_model')
    base_props.append('display_name')
    base_props.append('component_type_value')

    def __new__(cls, component_attribute_class_id, *args, **kwargs):
        if component_attribute_class_id in ComponentAttributeClass.by_id.keys():
            if not isinstance(ComponentAttributeClass.by_id[component_attribute_class_id], cls):
                raise Exception("Id already exists, not an actuator!")
            return ComponentAttributeClass.by_id[component_attribute_class_id]
        instance = super().__new__(cls, component_attribute_class_id=component_attribute_class_id)
        ComponentAttributeClass.by_id[component_attribute_class_id] = instance
        return instance

    def __init__(self,
                 component_attribute_class_id: Optional[str] = None,
                 actuator_type_value: Optional[str] = None,
                 display_name: Optional[str] = None,
                 make_model: Optional[str] = None):
        super(BooleanActuatorCac, self).__init__(component_attribute_class_id=component_attribute_class_id,
                                                 make_model=make_model,
                                                 display_name=display_name,
                                                 component_type_value=actuator_type_value)
        self.actuator_type_value = actuator_type_value
    
    def __repr__(self):
        val = f'PipeFlowSensorCac {self.make_model}: {self.display_name}'
        return val

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['component_attribute_class_id'] in ComponentAttributeClass.by_id.keys():
            raise DcError(f"component_attribute_class_id {attributes['component_attribute_class_id']} already in use")

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not attributes.get('component_attribute_class_id', None):
            raise DcError('component_attribute_class_id must exist')
        if not attributes.get('actuator_type_value', None):
            raise DcError('actuator_type_value')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        BooleanActuatorCac.check_uniqueness_of_primary_key(attributes)
        BooleanActuatorCac.check_existence_of_certain_attributes(attributes)
