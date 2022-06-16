"""Base for gt.spaceheat.status.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.gt.gt_spaceheat_sync_single.gt_spaceheat_sync_single_maker import GtSpaceheatSyncSingle
from schema.gt.gt_spaceheat_async_single.gt_spaceheat_async_single_maker import GtSpaceheatAsyncSingle


class GtSpaceheatStatusBase(NamedTuple):
    AboutGNodeAlias: str     #
    SlotStartUnixS: int     #
    ReportingPeriodS: int     #
    AsyncStatusList: List[GtSpaceheatAsyncSingle]
    SyncStatusList: List[GtSpaceheatSyncSingle]
    TypeAlias: str = 'gt.spaceheat.status.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        async_status_list = []
        for elt in self.AsyncStatusList:
            async_status_list.append(elt.asdict())
        d["AsyncStatusList"] = async_status_list
        sync_status_list = []
        for elt in self.SyncStatusList:
            sync_status_list.append(elt.asdict())
        d["SyncStatusList"] = sync_status_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.AboutGNodeAlias, str):
            errors.append(f"AboutGNodeAlias {self.AboutGNodeAlias} must have type str.")
        if not property_format.is_lrd_alias_format(self.AboutGNodeAlias):
            errors.append(f"AboutGNodeAlias {self.AboutGNodeAlias}"
                          " must have format LrdAliasFormat")
        if not isinstance(self.SlotStartUnixS, int):
            errors.append(f"SlotStartUnixS {self.SlotStartUnixS} must have type int.")
        if not isinstance(self.ReportingPeriodS, int):
            errors.append(f"ReportingPeriodS {self.ReportingPeriodS} must have type int.")
        if not isinstance(self.AsyncStatusList, list):
            errors.append(f"AsyncStatusesId {self.AsyncStatusList} must have type list.")
        else:
            for elt in self.AsyncStatusList:
                if not isinstance(elt, GtSpaceheatAsyncSingle):
                    errors.append(f"{elt} of self.AsyncStatusList must have type GtSpaceheatAsyncSingle.")
        if not isinstance(self.SyncStatusList, list):
            errors.append(f"SyncStatusesId {self.SyncStatusList} must have type list.")
        else:
            for elt in self.SyncStatusList:
                if not isinstance(elt, GtSpaceheatSyncSingle):
                    errors.append(f"{elt} of self.SyncStatusList must have type GtSpaceheatSyncSingle.")
        if self.TypeAlias != 'gt.spaceheat.status.100':
            errors.append(f"Type requires TypeAlias of gt.spaceheat.status.100, not {self.TypeAlias}.")
        
        return errors
