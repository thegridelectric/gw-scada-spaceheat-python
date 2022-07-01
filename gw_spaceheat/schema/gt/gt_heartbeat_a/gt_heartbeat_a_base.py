"""Base for gt.heartbeat.a.100"""
import json
from typing import List, NamedTuple


class GtHeartbeatABase(NamedTuple):
    TypeAlias: str = "gt.heartbeat.a.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.TypeAlias != "gt.heartbeat.a.100":
            errors.append(
                f"Type requires TypeAlias of gt.heartbeat.a.100, not {self.TypeAlias}."
            )

        return errors
