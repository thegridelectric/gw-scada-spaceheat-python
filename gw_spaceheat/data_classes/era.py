""" WorldInstanceEra Class Definition """
from typing import Optional
import time
import uuid
from data_classes.era_base import EraBase
from data_classes.errors import DcError
from data_classes.world_instance import WorldInstance  #


class Era(EraBase):
    by_idx = {}

    def __init__(self,
                 era_id: Optional[str] = None,
                 atomic_steps_per_time_step: Optional[int] = None,
                 creator_g_node_alias: Optional[str] = None,
                 time_is_throttled: Optional[bool] = None,
                 irl_expected_time_step_delta_milliseconds: Optional[int] = None,
                 index: Optional[int] = None,
                 first_time_step_index: Optional[int] = None,
                 last_time_step_index: Optional[float] = None,
                 world_instance_id: Optional[str] = None):
        super(Era, self).__init__(era_id=era_id,
                                  atomic_steps_per_time_step=atomic_steps_per_time_step,
                                  creator_g_node_alias=creator_g_node_alias,
                                  time_is_throttled=time_is_throttled,
                                  irl_expected_time_step_delta_milliseconds=irl_expected_time_step_delta_milliseconds,
                                  index=index,
                                  first_time_step_index=first_time_step_index,
                                  last_time_step_index=last_time_step_index,
                                  world_instance_id=world_instance_id)
        self.__class__.by_idx[self.index] = self

    def __repr__(self):
        rs = f'Era => WorldInstanceId: {self.world_instance_id}, TimeIsThrottled: {self.time_is_throttled}, AtomicStepsPerTimeStep: {self.atomic_steps_per_time_step}\n' + \
            f'IrlExpectedTimeStepDeltaMilliseconds: {self.irl_expected_time_step_delta_milliseconds}, Creator: {self.creator_g_node_alias}, Index: {self.index}, FirstTimeStepIndex: {self.first_time_step_index}' 
        if self.last_time_step_index: 
             rs += f' LastTimeStepIndex: {self.last_time_step_index}'

        return rs

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if 'era_id' not in attributes.keys():
            raise DcError('era_id must exist')
        if 'index' not in attributes.keys():
            raise DcError('index must exist ')
        if not attributes.get('atomic_steps_per_time_step', None):
            raise DcError('atomic_steps_per_time_step must exist')
        if not attributes.get('creator_g_node_alias', None):
            raise DcError('creator_g_node_alias must exist')
        if not attributes.get('world_instance_id', None):
            raise DcError('world_instance_id must exist')
        if not 'time_is_throttled' in attributes.keys():
            raise DcError('time_is_throttled must exist')
        if not attributes.get('irl_expected_time_step_delta_milliseconds', None):
            raise DcError('irl_expected_time_step_delta_milliseconds must exist')
        if 'first_time_step_index' not in attributes.keys():
            raise DcError('first_time_step_index must exist')

    @classmethod
    def check_initialization_consistency(cls, attributes):
        Era.check_uniqueness_of_primary_key(attributes)
        Era.check_existence_of_certain_attributes(attributes)
        Era.check_uniqueness_of_world_and_era_index(attributes)

    @classmethod
    def check_uniqueness_of_world_and_era_index(cls, attributes):
        """Axiom: No two eras can share the same WorldInstanceId and Index"""
        existing_eras = list(Era.by_id.values())
        this_world_eras = list(filter(lambda x: x.world_instance_id == attributes['world_instance_id'],existing_eras))
        same_index_this_world_eras = list(filter(lambda x: x.index == attributes['index'], this_world_eras))
        if len(same_index_this_world_eras) > 0:
            already = same_index_this_world_eras[0]
            raise DcError(f"Era for {attributes['world_instance_id']} and index {attributes['index']} already exists: {already.era_id}" )

    def check_immutability_for_existing_attributes(self, new_attributes):
        if self.era_id:
            if new_attributes['era_id'] != self.era_id:
                raise Exception('era_id is Immutable')
            if new_attributes['index'] != self.index:
                raise DcError('index is Immutable')
            if new_attributes['atomic_steps_per_time_step'] != self.atomic_steps_per_time_step:
                raise DcError('atomic_steps_per_time_step is Immutable')
            if new_attributes['creator_g_node_alias'] != self.creator_g_node_alias:
                raise DcError('creator_g_node_alias is Immutable')
            if new_attributes['world_instance_id'] != self.world_instance_id:
                raise DcError('world_instance_id is Immutable')
            if new_attributes[
                'irl_expected_time_step_delta_milliseconds'] != self.irl_expected_time_step_delta_milliseconds:
                raise DcError('irl_expected_time_step_delta_milliseconds is Immutable')
            if new_attributes['first_time_step_index'] != self.first_time_step_index:
                raise DcError('first_time_step_index is Immutable')
            if new_attributes['time_is_throttled'] != self.time_is_throttled:
                raise DcError('time_is_throttled is Immutable')
            if self.last_time_step_index:
                if new_attributes['last_time_step_index'] != self.last_time_step_index:
                    raise DcError('last_time_step_index is Immutable')

    def check_update_consistency(self, new_attributes):
        self.check_immutability_for_existing_attributes(new_attributes)

    """ Derived attributes """

    @property
    def name(self) -> str:
        """ CONCATENATE(WorldInstance,'_Era_',Index) """
        return self.world_instance_id + '_Era_' + f'{self.index}'

    @property
    def registry_name(self) -> str:
        return self.name

    """Static foreign objects referenced by their keys """

    @property
    def world_instance(self):
        if not (self.world_instance_id in WorldInstance.by_id.keys()):
            raise TypeError('WorldInstance is not loaded!')
        else:
            return WorldInstance.by_id[self.world_instance_id]
