"""gt.spaceheat.sync.single.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_spaceheat_sync_single.gt_spaceheat_sync_single_base import GtSpaceheatSyncSingleBase


class GtSpaceheatSyncSingle(GtSpaceheatSyncSingleBase):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.spaceheat.sync.single for {self}: {errors}")

    def hand_coded_errors(self):
        return []
