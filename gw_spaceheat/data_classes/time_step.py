""" TimeStep Class Definition """
import time
import uuid
from typing import Dict, Optional

import pendulum

from data_classes.era import Era
from data_classes.errors import DataClassLoadingError, DcError
from data_classes.world_instance import WorldInstance

from .time_step_base import TimeStepBase


class TimeStep(TimeStepBase):
    by_idx: Dict[int, TimeStepBase] = {}

    def __init__(self, time_step_id: Optional[str] = None,
                 irl_created_at_utc: time = time.time(),
                 previous_time_step_id: Optional[str] = None,
                 era_index: Optional[int] = None,
                 ts_index: Optional[int] = None,
                 era_id: Optional[str] = None):
        super(TimeStep, self).__init__(time_step_id=time_step_id,
                                       irl_created_at_utc=irl_created_at_utc,
                                       previous_time_step_id=previous_time_step_id,
                                       era_index=era_index,
                                       ts_index=ts_index,
                                       era_id=era_id)
        self.__class__.by_idx[self.ts_index] = self

    def __repr__(self):
            return f'TimeStep: time_unix_s {self.time_unix_s}, TimeUtc {self.time_utc} \n' +\
                 f'AtomicIndex: {self.atomic_index}, Eras AtomicStepsPerTimeStep {self.era.atomic_steps_per_time_step}, EraIndex {self.era_index}\n' +\
                 f'AtomicIndex is determined recursively by adding AtomicStepsPerTimeStep (property of era) to the AtomicIndex of the previous TimeStep.\n' +\
                 f'WorldInstance AtomicFrequency: {self.world_instance.atomic_frequency_hz}\n' +\
                 f'EraId: {self.previous_time_step_id}, era_id: {self.era_id}\n' +\
                 f'self.world_instance.start_time_unix_s {self.world_instance.start_time_unix_s} ({pendulum.from_timestamp(self.world_instance.start_time_unix_s)})'

    def check_existence_of_certain_attributes(cls, attributes):
        if not attributes.get('time_step_id', None):
            raise DcError('time_step_id must exist')
        if not attributes.get('era_id', None):
            raise DcError('era_id must exist')
        if 'era_index' not in attributes.keys():
            raise DcError('era_index must exist')
        if 'ts_index' not in attributes.keys():
            raise DcError('ts_index must exist')
        if not attributes.get('irl_created_at_utc', None):
            raise DcError('irl_created_at_utc must exist')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        TimeStep.check_uniqueness_of_primary_key(attributes)
        TimeStep.check_existence_of_certain_attributes(attributes)

    def check_immutability_for_existing_attributes(self, new_attributes):
        if self.time_step_id:
            if new_attributes['time_step_id'] != self.time_step_id:
                raise DcError('time_step_id is Immutable')
            if new_attributes['era_id'] != self.era_id:
                raise DcError('era_id is Immutable')
            if new_attributes['era_index'] != self.era_index:
                raise DcError('era_index is Immutable')
            if new_attributes['ts_index'] != self.ts_index:
                raise DcError('ts_index is Immutable')
            if new_attributes['irl_created_at_utc'] != self.irl_created_at_utc:
                raise DcError('irl_created_at_utc is Immutable')

    def check_update_consistency(self, new_attributes):
        self.check_immutability_for_existing_attributes(new_attributes)

    """ Derived attributes """

    @property
    def era(self) -> Era:
        if not(self.era_id in Era.by_id.keys()):
            raise DataClassLoadingError('WorldInstanceEra is not loaded!')
        else:
            return Era.by_id[self.era_id]

    @property
    def world_instance(self) -> WorldInstance:
        return self.era.world_instance


    @property
    def time_unix_ms(self) -> int:
        return int((self.world_instance.start_time_unix_s + (self.atomic_index/self.world_instance.atomic_frequency_hz)) * 1000)

    @property
    def time_unix_s(self) -> float:
        return self.time_unix_ms/1000

    @property
    def time_utc(self):
        return pendulum.from_timestamp(self.time_unix_s)

    @property
    def begins_era(self) -> bool:
        if self.era_index == 0:
            return True
        else:
            return False

    def seconds_since_prev_timestep(self) -> float:
        return self.era.atomic_steps_per_time_step/self.era.world_instance.atomic_frequency_hz

    @property
    def atomic_index(self) -> int:
        if self.previous_time_step_id is None:
            ans = 0
        else:
            if self.previous_time_step_id not in TimeStep.by_id.keys():
                raise Exception(f'time step {self.ts_index - 1} not in local TimeSteps! Calculating atomic index for '
                                f'time step {self.ts_index}')
            previous = TimeStep.by_id[self.previous_time_step_id]
            ans = previous.atomic_index + self.era.atomic_steps_per_time_step
        return ans
    """Static foreign objects referenced by their keys """
