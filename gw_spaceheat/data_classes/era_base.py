""" Era Base Class Definition """
from typing import Optional
from abc import ABC, abstractproperty
from data_classes.mixin import StreamlinedSerializerMixin


class EraBase(ABC, StreamlinedSerializerMixin):
    by_id = {}
    
    base_props = []
    base_props.append('era_id')
    base_props.append('atomic_steps_per_time_step')
    base_props.append('creator_g_node_alias')
    base_props.append('time_is_throttled')
    base_props.append('irl_expected_time_step_delta_milliseconds')
    base_props.append('index')
    base_props.append('first_time_step_index')
    base_props.append('last_time_step_index')
    base_props.append('world_instance_id')

    def __new__(cls, era_id, *args, **kwargs):
        try:
            return cls.by_id[era_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[era_id] = instance
            return instance

    def __init__(self,
                 era_id: Optional[str] = None,
                 atomic_steps_per_time_step: Optional[int] = None,
                 creator_g_node_alias: Optional[str] = None,
                 time_is_throttled: Optional[bool] = None,
                 irl_expected_time_step_delta_milliseconds: Optional[int] = None,
                 index: Optional[int] = None,
                 first_time_step_index: Optional[int] = None,
                 last_time_step_index: Optional[int] = None,
                 world_instance_id: Optional[str] = None):
        self.era_id = era_id
        self.atomic_steps_per_time_step = atomic_steps_per_time_step
        self.creator_g_node_alias = creator_g_node_alias
        self.time_is_throttled = time_is_throttled
        self.irl_expected_time_step_delta_milliseconds = irl_expected_time_step_delta_milliseconds
        self.index = index
        self.first_time_step_index = first_time_step_index
        self.last_time_step_index = last_time_step_index
        self.world_instance_id = world_instance_id

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['era_id'] in cls.by_id.keys():
            raise Exception(f"era_id {attributes['era_id']} already in use")

    @abstractproperty
    def name(self):
        """From Airtable Axioms:  """
        raise NotImplementedError

    @abstractproperty
    def registry_name(self):
        """From Airtable Axioms:  """
        raise NotImplementedError
