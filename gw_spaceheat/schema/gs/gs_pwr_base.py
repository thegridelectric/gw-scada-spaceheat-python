"""Base for GridWorks schema gs.pwr.100 with TypeAlias p"""
from typing import List, NamedTuple
import struct

import schema.property_format as property_format


class GsPwrBase(NamedTuple):  #
    Power: int
    TypeAlias: str = "p"

    def as_type(self) -> bytes:
        return struct.pack("<h", self.Power)

    def derived_errors(self) -> List[str]:
        errors = []
        if self.TypeAlias != "p":
            errors.append(f"Payload requires TypeAlias of p, not {self.TypeAlias}.")
        if not isinstance(self.Power, int):
            errors.append(f"Name {self.Power} must have type int")
        if not property_format.is_short_integer(self.Power):
            errors.append(
                f"Power {self.Power} does not work. Short format requires (-32767 -1) <= number <= 32767"
            )
        return errors
