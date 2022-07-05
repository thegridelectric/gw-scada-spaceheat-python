"""Base for gt.sh.cli.atn.cmd.110"""
import json
from typing import List, NamedTuple
import schema.property_format as property_format


class GtShCliAtnCmdBase(NamedTuple):
    FromGNodeAlias: str  #
    SendSnapshot: bool  #
    FromGNodeId: str  #
    TypeAlias: str = "gt.sh.cli.atn.cmd.110"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
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
        if not isinstance(self.SendSnapshot, bool):
            errors.append(
                f"SendSnapshot {self.SendSnapshot} must have type bool."
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
        if self.TypeAlias != "gt.sh.cli.atn.cmd.110":
            errors.append(
                f"Type requires TypeAlias of gt.sh.cli.atn.cmd.110, not {self.TypeAlias}."
            )

        return errors
