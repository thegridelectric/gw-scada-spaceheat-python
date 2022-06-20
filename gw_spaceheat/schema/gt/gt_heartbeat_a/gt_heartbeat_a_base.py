"""Base for gt.heartbeat.a"""
import json
from typing import List, Optional, NamedTuple
import schema.property_format as property_format


class GtHeartbeatABase(NamedTuple):
    TypeAlias: str = 'gt.heartbeat.a.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.TypeAlias != 'gt.heartbeat.a.100':
            errors.append(f"Type requires TypeAlias of gt.heartbeat.a.100, not {self.TypeAlias}.")
        
        return errors
