"""Makes gt.world.instance.200 type."""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus
from data_classes.world_instance import WorldInstance
from schema.gt.gnr.world_instance.gt_world_instance_2_0_0 import GtWorldInstance200
    
    
class GtWorldInstance200_Maker():
    mp_alias = 'gt.world.instance.200'
    mp_status = MpStatus.ACTIVE.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> GtWorldInstance200:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = 'gt.world.instance.200'
        if "IrlStartTimeUnixS" not in d.keys():
            d["IrlStartTimeUnixS"] = None
        if "StartTimeUnixS" not in d.keys():
            d["StartTimeUnixS"] = None
        if "WorldCoordinatorSupervisorContainerId" not in d.keys():
            d["WorldCoordinatorSupervisorContainerId"] = None
        if "AwsSnapShotId" not in d.keys():
            d["AwsSnapShotId"] = None
        if "RequestTimeUnixS" not in d.keys():
            d["RequestTimeUnixS"] = None
        if "WorldBrokerEc2InstanceId" not in d.keys():
            d["WorldBrokerEc2InstanceId"] = None
        if "EndTimeUnixS" not in d.keys():
            d["EndTimeUnixS"] = None
        if "IrlEndTimeUnixS" not in d.keys():
            d["IrlEndTimeUnixS"] = None
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None
        p = GtWorldInstance200(MpAlias=d["MpAlias"],
                        IrlStartTimeUnixS=d["IrlStartTimeUnixS"],
                        StartTimeUnixS=d["StartTimeUnixS"],
                        WorldCoordinatorSupervisorContainerId=d["WorldCoordinatorSupervisorContainerId"],
                        WorldRootGNodeAlias=d["WorldRootGNodeAlias"],
                        AwsSnapShotId=d["AwsSnapShotId"],
                        WorldInstanceId=d["WorldInstanceId"],
                        RequestTimeUnixS=d["RequestTimeUnixS"],
                        Idx=d["Idx"],
                        AtomicFrequencyHz=d["AtomicFrequencyHz"],
                        StartingGridRunClassAlias=d["StartingGridRunClassAlias"],
                        IsSimulated=d["IsSimulated"],
                        WorldBrokerEc2InstanceId=d["WorldBrokerEc2InstanceId"],
                        EndTimeUnixS=d["EndTimeUnixS"],
                        IrlEndTimeUnixS=d["IrlEndTimeUnixS"])
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p 

    @classmethod
    def data_class_to_schema_type(cls,dc:WorldInstance) -> GtWorldInstance200:
        if dc is None:
            return None
        candidate = GtWorldInstance200(MpAlias='gt.world.instance.200',
                        IrlStartTimeUnixS=dc.irl_start_time_unix_s,
                        StartTimeUnixS=dc.start_time_unix_s,
                        WorldCoordinatorSupervisorContainerId=dc.world_coordinator_supervisor_container_id,
                        WorldRootGNodeAlias=dc.world_root_g_node_alias,
                        AwsSnapShotId=dc.aws_snap_shot_id,
                        WorldInstanceId=dc.world_instance_id,
                        RequestTimeUnixS=dc.request_time_unix_s,
                        Idx=dc.idx,
                        AtomicFrequencyHz=dc.atomic_frequency_hz,
                        StartingGridRunClassAlias=dc.starting_grid_run_class_alias,
                        IsSimulated=dc.is_simulated,
                        WorldBrokerEc2InstanceId=dc.world_broker_ec2_instance_id,
                        EndTimeUnixS=dc.end_time_unix_s,
                        IrlEndTimeUnixS=dc.irl_end_time_unix_s)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:GtWorldInstance200) -> WorldInstance:
        if p is None:
            return None
        snake_dict = {}
        snake_dict['irl_start_time_unix_s']=p.IrlStartTimeUnixS
        snake_dict['start_time_unix_s']=p.StartTimeUnixS
        snake_dict['world_coordinator_supervisor_container_id']=p.WorldCoordinatorSupervisorContainerId
        snake_dict['world_root_g_node_alias']=p.WorldRootGNodeAlias
        snake_dict['aws_snap_shot_id']=p.AwsSnapShotId
        snake_dict['world_instance_id']=p.WorldInstanceId
        snake_dict['request_time_unix_s']=p.RequestTimeUnixS
        snake_dict['idx']=p.Idx
        snake_dict['atomic_frequency_hz']=p.AtomicFrequencyHz
        snake_dict['starting_grid_run_class_alias']=p.StartingGridRunClassAlias
        snake_dict['is_simulated']=p.IsSimulated
        snake_dict['world_broker_ec2_instance_id']=p.WorldBrokerEc2InstanceId
        snake_dict['end_time_unix_s']=p.EndTimeUnixS
        snake_dict['irl_end_time_unix_s']=p.IrlEndTimeUnixS
        if snake_dict['world_instance_id'] in WorldInstance.by_id.keys():
            world_instance = WorldInstance.by_id[snake_dict['world_instance_id']]
            try:
                world_instance.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning WorldInstance: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning WorldInstance: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(world_instance, key):
                    setattr(world_instance, key, value)
        else:
            world_instance = WorldInstance(**snake_dict)

        return world_instance

    @classmethod
    def type_is_valid(cls, object_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(object_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self,
                 world_root_g_node_alias: str,
                 world_instance_id: str,
                 idx: int,
                 atomic_frequency_hz: int,
                 starting_grid_run_class_alias: str,
                 is_simulated: bool,
                 irl_start_time_unix_s: Optional[int] = None ,
                 start_time_unix_s: Optional[int] = None ,
                 world_coordinator_supervisor_container_id: Optional[str] = None ,
                 aws_snap_shot_id: Optional[str] = None ,
                 request_time_unix_s: Optional[int] = None ,
                 world_broker_ec2_instance_id: Optional[str] = None ,
                 end_time_unix_s: Optional[int] = None ,
                 irl_end_time_unix_s: Optional[int] = None ):
        self.errors = []

        t = GtWorldInstance200(MpAlias=GtWorldInstance200_Maker.mp_alias,
                    IrlStartTimeUnixS=irl_start_time_unix_s,
                    StartTimeUnixS=start_time_unix_s,
                    WorldCoordinatorSupervisorContainerId=world_coordinator_supervisor_container_id,
                    WorldRootGNodeAlias=world_root_g_node_alias,
                    AwsSnapShotId=aws_snap_shot_id,
                    WorldInstanceId=world_instance_id,
                    RequestTimeUnixS=request_time_unix_s,
                    Idx=idx,
                    AtomicFrequencyHz=atomic_frequency_hz,
                    StartingGridRunClassAlias=starting_grid_run_class_alias,
                    IsSimulated=is_simulated,
                    WorldBrokerEc2InstanceId=world_broker_ec2_instance_id,
                    EndTimeUnixS=end_time_unix_s,
                    IrlEndTimeUnixS=irl_end_time_unix_s)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")
        self.type = t

