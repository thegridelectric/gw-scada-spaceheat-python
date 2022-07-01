"""Base for GridWorks schema gs.dispatch.100 with TypeAlias d"""
from typing import List, NamedTuple
import struct

import schema.property_format as property_format


class GsDispatchBase(NamedTuple):
    RelayState: int
    TypeAlias: str = "d"

    def as_type(self) -> bytes:
        return struct.pack("<h", self.RelayState)

    def derived_errors(self) -> List[str]:
        errors = []
        if self.TypeAlias != "d":
            errors.append(f"Payload requires TypeAlias of d, not {self.TypeAlias}.")
        if not isinstance(self.RelayState, int):
            errors.append(f"Name {self.RelayState} must have type int")
        if not property_format.is_bit(self.RelayState):
            errors.append(f"RelayState {self.RelayState} must be 0 or 1")
        return errors
