"""Base for GridWorks schema gs.dispatch.100 with MpAlias d"""
from typing import List, Dict, Tuple, Optional, NamedTuple
import datetime
import enum
import struct

import schema.property_format as property_format

class GsDispatch100Base(NamedTuple):   #
    Power: int     # 
    MpAlias: str = 'd'

    def asbinary(self) -> bytes:
        return struct.pack("<h", self.Power)

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'd':
            is_valid = False
            errors.append(f"Payload requires MpAlias of d, not {self.MpAlias}.")
        if not isinstance(self.Power, int):
            is_valid = False
            errors.append(f"Name {self.Power} must have type int")
        if not property_format.is_short_integer(self.Power):
            is_valid = False
            errors.append(f"Power {self.Power} does not work. Short format requires (-32767 -1) <= number <= 32767")
        return is_valid, errors

