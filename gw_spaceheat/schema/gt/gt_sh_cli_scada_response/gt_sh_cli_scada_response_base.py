"""Base for gt.sh.cli.scada.response.100"""
import json
from typing import List, NamedTuple
from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot_maker import GtShStatusSnapshot


class GtShCliScadaResponseBase(NamedTuple):
    Snapshot: GtShStatusSnapshot  #
    TypeAlias: str = "gt.sh.cli.scada.response.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        d["Snapshot"] = self.Snapshot.asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.Snapshot, GtShStatusSnapshot):
            errors.append(
                f"Snapshot {self.Snapshot} must have typeGtShStatusSnapshot."
            )
        if self.TypeAlias != "gt.sh.cli.scada.response.100":
            errors.append(
                f"Type requires TypeAlias of gt.sh.cli.scada.response.100, not {self.TypeAlias}."
            )

        return errors
