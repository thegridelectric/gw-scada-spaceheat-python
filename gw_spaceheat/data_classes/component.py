""" SCADA Component Class Definition """

from abc import ABC
from typing import Optional, Dict

from data_classes.mixin import StreamlinedSerializerMixin
from data_classes.component_attribute_class import ComponentAttributeClass


class Component(ABC, StreamlinedSerializerMixin):
    by_id: Dict[str, "Component"] = {}
    base_props = []
    base_props.append('component_id')
    base_props.append('display_name')
    base_props.append('component_attribute_class_id')
    base_props.append('hw_uid')

    def __new__(cls, component_id, *args, **kwargs):
        try:
            return cls.by_id[component_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[component_id] = instance
            return instance

    def __init__(self,
                 component_id: str,
                 component_attribute_class_id: str,
                 display_name: Optional[str] = None,
                 hw_uid: Optional[str] = None):
        self.component_id = component_id
        self.display_name = display_name
        self.component_attribute_class_id = component_attribute_class_id
        self.hw_uid = hw_uid

    @property
    def component_attribute_class(self) -> ComponentAttributeClass:
        return ComponentAttributeClass.by_id[self.component_attribute_class_id]
