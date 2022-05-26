""" ComponentCategory Base Class Definition """

from abc import ABC, abstractproperty
from typing import Optional

from data_classes.mixin import StreamlinedSerializerMixin


class ComponentCategoryBase(ABC, StreamlinedSerializerMixin):
    by_id = {}
    
    base_props = []
    base_props.append('value')
    base_props.append('color_hex')

    def __new__(cls, value, *args, **kwargs):
        try:
            return cls.by_id[value]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[value] = instance
            return instance

    def __init__(self,
                 value: Optional[str] = None,
                 color_hex: Optional[str] = None):
        self.value = value
        self.color_hex = color_hex

    """ Derived attributes """
