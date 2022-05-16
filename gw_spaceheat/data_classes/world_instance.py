""" WorldInstance Class Definition """
import json
from data_classes.errors import DcError, DataClassLoadingError
import pendulum
from data_classes.world_instance_base import WorldInstanceBase
import time


class WorldInstance(WorldInstanceBase):

    def __repr__(self):
        rs = f'WorldInstance {self.world_instance_id} =>  IsSimulated: {self.is_simulated}, IsSubSecondSim: {self.is_sub_second_sim}, AtomicFrequencyHz: {self.atomic_frequency_hz}, \n' 
        if self.start_time_unix_s:
            rs += f'StartTime: {pendulum.from_timestamp(self.start_time_unix_s)}, '
        if self.end_time_unix_s:
            rs += f'EndTime: {pendulum.from_timestamp(self.end_time_unix_s)}, '
        if self.irl_start_time_unix_s:
            rs += f'IrlStartTime: {pendulum.from_timestamp(self.irl_start_time_unix_s)}, '
        if self.request_time_unix_s:
            rs += f'RequestTime: {pendulum.from_timestamp(self.request_time_unix_s)}, '
        if self.irl_end_time_unix_s:
            rs += f'IrlEndTime: {pendulum.from_timestamp(self.irl_end_time_unix_s)}, '
        if self.aws_snap_shot_id:
            rs += f'AwsSnapShotId: {self.aws_snap_shot_id},'
        if self.world_broker_ec2_instance_id:
            rs += f'WorldBrokerEc2InstanceId: {self.world_broker_ec2_instance_id}'
        rs += f'SupervisorContainerId: {self.world_coordinator_supervisor_container_id}'

        return rs

    @classmethod
    def load_all(cls):
        def load_all(cls):
            """ generates request to WorldCoordinator"""
            raise NotImplementedError

    @classmethod
    def check_existence_of_certain_attributes(cls, attributes):
        if not attributes.get('world_instance_id', None):
            raise Exception('world_instance_id must exist')
        if not attributes.get('world_root_g_node_alias', None):
            raise Exception('world_root_g_node_alias must exist')
        if not attributes.get('idx', None):
            raise Exception('idx must exist')
        if not attributes.get('atomic_frequency_hz', None):
            raise Exception('atomic_frequency_hz must exist')
        if 'is_sub_second_sim' not in attributes.keys():
            raise Exception('is_sub_second_sim must exist')
        if 'is_simulated' not in attributes.keys():
            raise Exception('is_simulated must exist')
        #Issue: the following gets triggered by wi.is_simulated = False
        #if not attributes.get('is_simulated', None):
        #    raise Exception(f'is_simulated must exist: {attributes}')
        if not attributes.get('starting_grid_run_class_alias', None):
            raise Exception('starting_grid_run_class_alias must exist')

    @classmethod
    def check_atomic_frequency(cls, attributes):
        if attributes['is_simulated'] is True and attributes['is_sub_second_sim'] is False and attributes['atomic_frequency_hz'] != 1:
            raise Exception(f"If world is simulated but not subsecond then atomic frequency hz must be 1. Got {attributes['atomic_frequency_hz']}")

    @classmethod
    def check_initialization_consistency(cls, attributes):
        WorldInstance.check_uniqueness_of_primary_key(attributes)
        WorldInstance.check_existence_of_certain_attributes(attributes)
        WorldInstance.check_atomic_frequency(attributes)

    def check_immutability_for_existing_attributes(self, new_attributes):
        if self.world_instance_id:
            if new_attributes['world_instance_id'] != self.world_instance_id:
                raise DcError('world_instance_id is Immutable')
            if new_attributes['world_root_g_node_alias'] != self.world_root_g_node_alias:
                raise DcError('world_root_g_node_alias is Immutable')
            if new_attributes['idx'] != self.idx:
                raise DcError('idx is Immutable')
            if new_attributes['is_simulated'] != self.is_simulated:
                raise DcError('is_simulated is Immutable')
            if new_attributes['atomic_frequency_hz'] != self.atomic_frequency_hz:
                raise DcError('atomic_frequency_hz')
        if self.start_time_unix_s:
            if new_attributes['start_time_unix_s'] != self.start_time_unix_s:
                raise DcError('start_time_unix_s is Immutable')
        if self.request_time_unix_s:
            if new_attributes['request_time_unix_s'] != self.request_time_unix_s:
                raise DcError('request_time_unix_s is Immutable')
        if self.irl_end_time_unix_s:
            if new_attributes['irl_nd_time_unix_s'] != self.irl_end_time_unix_s:
                raise DcError('irl_end_time_unix_s is Immutable')
        if self.irl_start_time_unix_s:
            if new_attributes['irl_start_time_unix_s'] != self.irl_start_time_unix_s:
                raise DcError('irl_start_time_unix_s is Immutable')
        if self.starting_grid_run_class_alias:
            if new_attributes['starting_grid_run_class_alias'] != self.starting_grid_run_class_alias:
                raise DcError('starting_grid_run_class_alias is Immutable')


    def check_update_consistency(self, new_attributes):
        self.check_immutability_for_existing_attributes(new_attributes)

    """ Derived attributes """

    @property
    def alias(self) -> str:
        return self.world_root_g_node_alias + '__' + str(self.idx)

    @property
    def start_time_utc(self) -> str:
        raise NotImplementedError

    @property
    def registry_name(self) -> str:
        return self.alias

    @property
    def irl_start_time_utc(self) -> str:
        raise NotImplementedError

    @property
    def world_coordinator_supervisor_container(self) -> str:
        raise NotImplementedError

    @property
    def component_registry_alias(self) -> str:
        if self.universe == 'dev':
            return 'dgwps.cr'
        elif self.universe == 'shadow':
            return 'sgwps.cr'
        else:
            raise NotImplementedError("Only universes w component registries are dev and shadow")

    @property
    def gnr_alias(self) -> str:
        if self.universe == 'dev':
            return 'dgwps.gnr'
        elif self.universe == 'shadow':
            return 'sgwps.gnr'
        else:
            raise NotImplementedError("Only universes w component registries are dev and shadow")

    @property
    def wir_alias(self) -> str:
        if self.universe == 'dev':
            return 'dgwps.wir'
        elif self.universe == 'shadow':
            return 'sgwps.wir'
        else:
            raise NotImplementedError("Only universes w world instance registries are dev and shadow")

    @property
    def universe(self) -> str:
        if self.alias.startswith('d'):
            return 'dev'
        elif self.alias.startswith('s'):
            return 'shadow'
        elif self.alias.startswith('h'):
            return 'hybrid'
        elif self.alias.starstwith('p'):
            return 'production'
        else:
            return None

    @property
    def universe_domain_name(self) -> str:
        #TODO: access the UNIVERSE_DOMAIN_NAME config variables in gw-platform-common/docker/container_data
        if self.universe == 'dev':
            return 'gridworks-consulting.com'
        if self.universe == 'shadow':
            return 'electricity.works'
        else:
            print('Only recognized universes are dev and shadow')
            raise NotImplementedError

    @property
    def wc_subdomain_word(self) -> str:
        return 'wc-'+'-'.join(self.alias.split('__'))

    @property
    def wc_fqdn(self) -> str:
        return self.wc_subdomain_word + '.' + self.universe_domain_name

    @property
    def rabbit_fqdn(self) -> str:
        return '-'.join(self.alias.split('__')) + '.' + self.universe_domain_name

    @property
    def has_started(self) -> bool:
        if not self.irl_start_time_unix_s:
            return False
        now = time.time()
        if self.irl_start_time_unix_s > now:
            raise Exception(f'Current time is {pendulum.from_timestamp(now)}. World Instance claim a '
                                f'start time {pendulum.from_timestamp(self.irl_start_time_unix_s)} '
                                f'which is in the future! ')
        return True

    """Static foreign objects referenced by their keys """


