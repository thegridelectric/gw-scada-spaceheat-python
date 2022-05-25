""" TimeStep Base Class Definition """
import time
import uuid
from abc import ABC, abstractproperty
from typing import Optional

from data_classes.mixin import StreamlinedSerializerMixin


class TimeStepBase(ABC, StreamlinedSerializerMixin):
    by_id = {}
    
    base_props = []
    base_props.append('time_step_id')
    base_props.append('irl_created_at_utc')
    base_props.append('previous_time_step_id')
    base_props.append('era_index')
    base_props.append('ts_index')
    base_props.append('era_id')

    def __new__(cls, time_step_id, *args, **kwargs):
        try:
            return cls.by_id[time_step_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[time_step_id] = instance
            return instance

    def __init__(self,
                 time_step_id: Optional[str] = None,
                 irl_created_at_utc: time = time.time(),
                 previous_time_step_id: Optional[str] = None,
                 era_index: Optional[int] = None,
                 ts_index: Optional[int] = None,
                 era_id: Optional[str] = None):
        self.time_step_id = time_step_id
        self.irl_created_at_utc = irl_created_at_utc
        self.previous_time_step_id = previous_time_step_id
        self.era_index = era_index
        self.ts_index = ts_index
        self.era_id = era_id

    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['time_step_id'] in cls.by_id.keys():
            raise Exception(f"time_step_id {attributes['time_step_id']} already in use")


    """ Derived attributes """

    @abstractproperty
    def world_instance(self):
        """From Airtable Axioms:  """
        raise NotImplementedError

    @abstractproperty
    def begins_era(self):
        """From Airtable Axioms:  """
        raise NotImplementedError

    @abstractproperty
    def atomic_index(self):
        """From Airtable Axioms:  """
        raise NotImplementedError

    @abstractproperty
    def time_unix_ms(self):
        """From Airtable Axioms:  """
        raise NotImplementedError

    @abstractproperty
    def time_unix_s(self):
        """From Airtable Axioms:  """
        raise NotImplementedError
