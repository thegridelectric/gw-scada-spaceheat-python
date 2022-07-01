"""Base for gt.sh.cli.atn.cmd.100"""
import json
from typing import List, NamedTuple


class GtShCliAtnCmdBase(NamedTuple):
    SendSnapshot: bool  #
    TypeAlias: str = "gt.sh.cli.atn.cmd.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.SendSnapshot, bool):
            errors.append(
                f"SendSnapshot {self.SendSnapshot} must have type bool."
            )
        if self.TypeAlias != "gt.sh.cli.atn.cmd.100":
            errors.append(
                f"Type requires TypeAlias of gt.sh.cli.atn.cmd.100, not {self.TypeAlias}."
            )

        return errors
