"""Base for gt.sh.cli.scada.response.110"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format
from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot_maker import GtShStatusSnapshot


class GtShCliScadaResponseBase(NamedTuple):
    FromGNodeAlias: str  #
    FromGNodeId: str  #
    Snapshot: GtShStatusSnapshot  #
    TypeAlias: str = "gt.sh.cli.scada.response.110"

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
        if not isinstance(self.FromGNodeId, str):
            errors.append(
                f"FromGNodeId {self.FromGNodeId} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.FromGNodeId):
            errors.append(
                f"FromGNodeId {self.FromGNodeId}"
                " must have format UuidCanonicalTextual"
            )
        if not isinstance(self.Snapshot, GtShStatusSnapshot):
            errors.append(
                f"Snapshot {self.Snapshot} must have typeGtShStatusSnapshot."
            )
        if self.TypeAlias != "gt.sh.cli.scada.response.110":
            errors.append(
                f"Type requires TypeAlias of gt.sh.cli.scada.response.110, not {self.TypeAlias}."
            )

        return errors
