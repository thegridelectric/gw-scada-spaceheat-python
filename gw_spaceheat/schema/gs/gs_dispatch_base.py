"""Base for GridWorks schema gs.dispatch.100 with TypeAlias d"""
from typing import List, Dict, Tuple, Optional, NamedTuple
import datetime
import enum
import struct

import schema.property_format as property_format

class GsDispatchBase(NamedTuple):   #
    Power: int     # 
    TypeAlias: str = 'd'

    def as_type(self) -> bytes:
        return struct.pack("<h", self.Power)

    def derived_errors(self) -> Tuple[bool, Optional[List[str]]]:
        errors = []
        if self.TypeAlias != 'd':
            errors.append(f"Payload requires MpAlias of d, not {self.TypeAlias}.")
        if not isinstance(self.Power, int):
            errors.append(f"Name {self.Power} must have type int")
        if not property_format.is_short_integer(self.Power):
            errors.append(f"Power {self.Power} does not work. Short format requires (-32767 -1) <= number <= 32767")
        return errors
