"""Base for snapshot.spaceheat.100"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.gt.telemetry_snapshot_spaceheat.telemetry_snapshot_spaceheat_maker import TelemetrySnapshotSpaceheat


class SnapshotSpaceheatBase(NamedTuple):
    FromGNodeAlias: str  #
    FromGNodeInstanceId: str  #
    Snapshot: TelemetrySnapshotSpaceheat  #
    TypeAlias: str = "snapshot.spaceheat.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        d["Snapshot"] = self.Snapshot.asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.FromGNodeAlias, str):
            errors.append(
                f"FromGNodeAlias {self.FromGNodeAlias} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.FromGNodeAlias):
            errors.append(
                f"FromGNodeAlias {self.FromGNodeAlias}"
                " must have format LrdAliasFormat"
            )
        if not isinstance(self.FromGNodeInstanceId, str):
            errors.append(
                f"FromGNodeInstanceId {self.FromGNodeInstanceId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.FromGNodeInstanceId):
            errors.append(
                f"FromGNodeInstanceId {self.FromGNodeInstanceId}"
                " must have format UuidCanonicalTextual"
            )
        if not isinstance(self.Snapshot, TelemetrySnapshotSpaceheat):
            errors.append(
                f"Snapshot {self.Snapshot} must have typeTelemetrySnapshotSpaceheat."
            )
        if self.TypeAlias != "snapshot.spaceheat.100":
            errors.append(
                f"Type requires TypeAlias of snapshot.spaceheat.100, not {self.TypeAlias}."
            )

        return errors
