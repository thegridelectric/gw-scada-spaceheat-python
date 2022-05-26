""" WorldInstance Base Class Definition """

from abc import ABC, abstractproperty
from typing import Optional

from data_classes.mixin import StreamlinedSerializerMixin


class WorldInstanceBase(ABC, StreamlinedSerializerMixin):
    by_id = {}
    by_alias = {}
    base_props = []
    base_props.append('world_instance_id')
    base_props.append('world_root_g_node_alias')
    base_props.append('start_time_unix_s')
    base_props.append('is_simulated')
    base_props.append('atomic_frequency_hz')
    base_props.append('request_time_unix_s')
    base_props.append('irl_start_time_unix_s')
    base_props.append('world_coordinator_supervisor_container_id')
    base_props.append('idx')
    base_props.append('starting_grid_run_class_alias')
    base_props.append('irl_end_time_unix_s')
    base_props.append('aws_snap_shot_id')
    base_props.append('world_broker_ec2_instance_id')
    base_props.append('is_sub_second_sim')
    base_props.append('end_time_unix_s')

    def __new__(cls, world_instance_id, *args, **kwargs):
        try:
            return cls.by_id[world_instance_id]
        except KeyError:
            instance = super().__new__(cls)
            cls.by_id[world_instance_id] = instance
            return instance

    def __init__(self,
                 world_instance_id: Optional[str] = None,
                 world_root_g_node_alias: Optional[str] = None,
                 start_time_unix_s: Optional[int] = None,
                 is_simulated: Optional[bool] = None,
                 atomic_frequency_hz: Optional[int] = None,
                 request_time_unix_s: Optional[int] = None,
                 irl_start_time_unix_s: Optional[int] = None,
                 world_coordinator_supervisor_container_id: Optional[str] = None,
                 idx: Optional[int] = None,
                 starting_grid_run_class_alias: Optional[str] = None,
                 irl_end_time_unix_s: Optional[int] = None,
                 aws_snap_shot_id: Optional[str] = None,
                 world_broker_ec2_instance_id: Optional[str] = None,
                 is_sub_second_sim: Optional[bool] = None,
                 end_time_unix_s: Optional[int] = None):
        self.world_instance_id = world_instance_id
        self.world_root_g_node_alias = world_root_g_node_alias
        self.start_time_unix_s = start_time_unix_s
        self.is_simulated = is_simulated
        self.atomic_frequency_hz = atomic_frequency_hz
        self.request_time_unix_s = request_time_unix_s
        self.irl_start_time_unix_s = irl_start_time_unix_s
        self.world_coordinator_supervisor_container_id = world_coordinator_supervisor_container_id
        self.idx = idx
        self.starting_grid_run_class_alias = starting_grid_run_class_alias
        self.irl_end_time_unix_s = irl_end_time_unix_s
        self.aws_snap_shot_id = aws_snap_shot_id
        self.world_broker_ec2_instance_id = world_broker_ec2_instance_id
        self.is_sub_second_sim = is_sub_second_sim
        self.end_time_unix_s = end_time_unix_s
        self.__class__.by_alias[self.alias] = self

            
    @classmethod
    def check_uniqueness_of_primary_key(cls, attributes):
        if attributes['world_instance_id'] in cls.by_id.keys():
            raise Exception(f"world_instance_id {attributes['world_instance_id']} already in use")


    """ Derived attributes """

    @abstractproperty
    def alias(self):
        """From Airtable Axioms:  """
        raise NotImplementedError

    @abstractproperty
    def start_time_utc(self):
        """From Airtable Axioms: Derived from WorldInstance.StartTimeUnixS. It represents, in UTC, the  
        first time of the first time stamp of the World Instance. """
        raise NotImplementedError

    @abstractproperty
    def registry_name(self):
        """From Airtable Axioms: Alias """
        raise NotImplementedError

    @abstractproperty
    def irl_start_time_utc(self):
        """From Airtable Axioms: IrlStartTimeUtc is derived from WorldInstance.IrlStartTimeUnixS - the start 
        time, in UTC format, for the simulation In Real Life (as opposed to the 
        first time in simulated time). None if IsSimulated is False. """
        raise NotImplementedError

    @abstractproperty
    def world_coordinator_supervisor_container(self):
        """From Airtable Axioms:  """
        raise NotImplementedError

    @abstractproperty
    def world_root_g_node(self):
        """From Airtable Axioms: There is a commutative diagram here.  This GNode must be the GNode whose 
        alias is WorldRootGNodeAlias at the IrlStartTime of the World Instance. 
        It must also be the WorldCoordinatorSupervisorContainer.SupervisorGNode """
        raise NotImplementedError
