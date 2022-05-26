""" ComponentSubCategory Base Class Definition """

from abc import ABC, abstractproperty
from typing import Optional

from data_classes.mixin import StreamlinedSerializerMixin


class ComponentSubCategoryBase(ABC, StreamlinedSerializerMixin):
    by_id = {}
    
    base_props = []
    base_props.append('value')
    base_props.append('component_category_value')

    def __new__(cls, value, *args, **kwargs):
        try:
            return cls.by_id[value]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[value] = instance
            return instance

    def __init__(self,
                 value: Optional[str] = None,
                 component_category_value: Optional[str] = None):
        self.value = value
        self.component_category_value = component_category_value

    """ Derived attributes """
