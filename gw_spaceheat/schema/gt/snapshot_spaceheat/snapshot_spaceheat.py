"""snapshot.spaceheat.100 type"""

from schema.errors import MpSchemaError
from schema.gt.snapshot_spaceheat.snapshot_spaceheat_base import (
    SnapshotSpaceheatBase,
)


class SnapshotSpaceheat(SnapshotSpaceheatBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making snapshot.spaceheat.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
