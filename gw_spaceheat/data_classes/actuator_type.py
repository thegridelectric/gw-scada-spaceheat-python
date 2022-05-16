""" ActuatorType Class Definition """
from typing import Optional
from abc import ABC
from .mixin import StreamlinedSerializerMixin


class ActuatorType(ABC, StreamlinedSerializerMixin):
    by_id = {}
    
    base_props = []
    base_props.append('value')
    base_props.append('display_name')

    def __new__(cls, value, *args, **kwargs):
        try:
            return cls.by_id[value]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[value] = instance
            return instance

    def __init__(self,
                 value: Optional[str] = None,
                 display_name: Optional[str] = None):
        self.value = value
        self.display_name = display_name
