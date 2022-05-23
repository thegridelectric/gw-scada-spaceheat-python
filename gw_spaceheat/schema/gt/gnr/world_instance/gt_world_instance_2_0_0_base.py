"""Base for gt.world.instance.200"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format


class GtWorldInstance200Base(NamedTuple):
    WorldRootGNodeAlias: str     #
    WorldInstanceId: str     #
    Idx: int     #
    AtomicFrequencyHz: int     #
    StartingGridRunClassAlias: str     #
    IsSimulated: bool     #
    IrlStartTimeUnixS: Optional[int] = None
    StartTimeUnixS: Optional[int] = None
    WorldCoordinatorSupervisorContainerId: Optional[str] = None
    AwsSnapShotId: Optional[str] = None
    RequestTimeUnixS: Optional[int] = None
    WorldBrokerEc2InstanceId: Optional[str] = None
    EndTimeUnixS: Optional[int] = None
    IrlEndTimeUnixS: Optional[int] = None
    MpAlias: str = 'gt.world.instance.200'

    def asdict(self):
        d = self._asdict()
        if d["IrlStartTimeUnixS"] is None:
            del d["IrlStartTimeUnixS"]
        if d["StartTimeUnixS"] is None:
            del d["StartTimeUnixS"]
        if d["WorldCoordinatorSupervisorContainerId"] is None:
            del d["WorldCoordinatorSupervisorContainerId"]
        if d["AwsSnapShotId"] is None:
            del d["AwsSnapShotId"]
        if d["RequestTimeUnixS"] is None:
            del d["RequestTimeUnixS"]
        if d["WorldBrokerEc2InstanceId"] is None:
            del d["WorldBrokerEc2InstanceId"]
        if d["EndTimeUnixS"] is None:
            del d["EndTimeUnixS"]
        if d["IrlEndTimeUnixS"] is None:
            del d["IrlEndTimeUnixS"]
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.world.instance.200':
            is_valid = False
            errors.append(f"Type requires MpAlias of gt.world.instance.200, not {self.MpAlias}.")
        if not isinstance(self.WorldRootGNodeAlias, str):
            is_valid = False
            errors.append(f"WorldRootGNodeAlias {self.WorldRootGNodeAlias} must have type str.")
        if not schema.property_format.is_g_node_lrd_alias_format(self.WorldRootGNodeAlias):
            is_valid = False
            errors.append(f"WorldRootGNodeAlias {self.WorldRootGNodeAlias} must have format GNodeLrdAliasFormat.")
        if not isinstance(self.WorldInstanceId, str):
            is_valid = False
            errors.append(f"WorldInstanceId {self.WorldInstanceId} must have type str.")
        if not schema.property_format.is_world_instance_alias_format(self.WorldInstanceId):
            is_valid = False
            errors.append(f"WorldInstanceId {self.WorldInstanceId} must have format WorldInstanceAliasFormat.")
        if not isinstance(self.Idx, int):
            is_valid = False
            errors.append(f"Idx {self.Idx} must have type int.")
        if not isinstance(self.AtomicFrequencyHz, int):
            is_valid = False
            errors.append(f"AtomicFrequencyHz {self.AtomicFrequencyHz} must have type int.")
        if not isinstance(self.StartingGridRunClassAlias, str):
            is_valid = False
            errors.append(f"StartingGridRunClassAlias {self.StartingGridRunClassAlias} must have type str.")
        if not schema.property_format.is_grid_run_class_alias_format(self.StartingGridRunClassAlias):
            is_valid = False
            errors.append(f"StartingGridRunClassAlias {self.StartingGridRunClassAlias} must have format GridRunClassAliasFormat.")
        if not isinstance(self.IsSimulated, bool):
            is_valid = False
            errors.append(f"IsSimulated {self.IsSimulated} must have type bool.")
        if self.IrlStartTimeUnixS:
            if not isinstance(self.IrlStartTimeUnixS, int):
                is_valid = False
                errors.append(f"IrlStartTimeUnixS {self.IrlStartTimeUnixS} must have type int.")
            if not schema.property_format.is_non_negative_int64(self.IrlStartTimeUnixS):
                is_valid = False
                errors.append(f"IrlStartTimeUnixS {self.IrlStartTimeUnixS} must have format NonNegativeInt64.")
        if self.StartTimeUnixS:
            if not isinstance(self.StartTimeUnixS, int):
                is_valid = False
                errors.append(f"StartTimeUnixS {self.StartTimeUnixS} must have type int.")
            if not schema.property_format.is_non_negative_int64(self.StartTimeUnixS):
                is_valid = False
                errors.append(f"StartTimeUnixS {self.StartTimeUnixS} must have format NonNegativeInt64.")
        if self.WorldCoordinatorSupervisorContainerId:
            if not isinstance(self.WorldCoordinatorSupervisorContainerId, str):
                is_valid = False
                errors.append(f"WorldCoordinatorSupervisorContainerId {self.WorldCoordinatorSupervisorContainerId} must have type str.")
            if not schema.property_format.is_uuid_canonical_textual(self.WorldCoordinatorSupervisorContainerId):
                is_valid = False
                errors.append(f"WorldCoordinatorSupervisorContainerId {self.WorldCoordinatorSupervisorContainerId} must have format UuidCanonicalTextual.")
        if self.AwsSnapShotId:
            if not isinstance(self.AwsSnapShotId, str):
                is_valid = False
                errors.append(f"AwsSnapShotId {self.AwsSnapShotId} must have type str.")
        if self.RequestTimeUnixS:
            if not isinstance(self.RequestTimeUnixS, int):
                is_valid = False
                errors.append(f"RequestTimeUnixS {self.RequestTimeUnixS} must have type int.")
            if not schema.property_format.is_non_negative_int64(self.RequestTimeUnixS):
                is_valid = False
                errors.append(f"RequestTimeUnixS {self.RequestTimeUnixS} must have format NonNegativeInt64.")
        if self.WorldBrokerEc2InstanceId:
            if not isinstance(self.WorldBrokerEc2InstanceId, str):
                is_valid = False
                errors.append(f"WorldBrokerEc2InstanceId {self.WorldBrokerEc2InstanceId} must have type str.")
        if self.EndTimeUnixS:
            if not isinstance(self.EndTimeUnixS, int):
                is_valid = False
                errors.append(f"EndTimeUnixS {self.EndTimeUnixS} must have type int.")
            if not schema.property_format.is_non_negative_int64(self.EndTimeUnixS):
                is_valid = False
                errors.append(f"EndTimeUnixS {self.EndTimeUnixS} must have format NonNegativeInt64.")
        if self.IrlEndTimeUnixS:
            if not isinstance(self.IrlEndTimeUnixS, int):
                is_valid = False
                errors.append(f"IrlEndTimeUnixS {self.IrlEndTimeUnixS} must have type int.")
            if not schema.property_format.is_non_negative_int64(self.IrlEndTimeUnixS):
                is_valid = False
                errors.append(f"IrlEndTimeUnixS {self.IrlEndTimeUnixS} must have format NonNegativeInt64.")
        return is_valid, errors

