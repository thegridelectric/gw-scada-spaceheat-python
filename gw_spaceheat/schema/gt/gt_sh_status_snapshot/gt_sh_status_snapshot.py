"""gt.sh.status.snapshot.110 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot_base import (
    GtShStatusSnapshotBase,
)


class GtShStatusSnapshot(GtShStatusSnapshotBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.sh.status.snapshot.110 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
