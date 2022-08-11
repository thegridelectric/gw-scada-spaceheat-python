"""telemetry.snapshot.spaceheat.100 type"""

from schema.errors import MpSchemaError
from schema.gt.telemetry_snapshot_spaceheat.telemetry_snapshot_spaceheat_base import (
    TelemetrySnapshotSpaceheatBase,
)


class TelemetrySnapshotSpaceheat(TelemetrySnapshotSpaceheatBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making telemetry.snapshot.spaceheat.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
