"""Base for gt.power.sync.1_0_0"""
from typing import List, Dict, Tuple, Optional, NamedTuple
import datetime
import enum
import struct

from .property_format import is_reasonable_unix_time_ms


class AccuracyCategory(enum.Enum):
    ANSI12_20__0_5 = "Ansi12.20__0.5"
    PROBABLY__1_5 = "Probably__1.5"

class GtPowerSync100PayloadBase(NamedTuple):
    SlotStartUnixS: int   
    SlotDurationS: int
    PowerWList: List[int]
    ScadaReadTimeUnixMsList: List[int]
    WithdrawalPostive: bool
    WExponent: int
    AccuracyCategory: AccuracyCategory
    ValidationUid: str
    MpAlias: str = 'gt.power.sync.1_0_0'

    def asdict(self):
        d = self._asdict()
        return d

    def is_accuracy_category(self, candidate):
        try:
            AccuracyCategory(candidate)
        except ValueError:
            return False
        return True


    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != 'gt.power.sync.1_0_0':
            is_valid = False
            errors.append(f"Payload requires MpAlias of gt.power.sync.1_0_0, not {self.MpAlias}.")
        if not isinstance(self.SlotStartUnixS, int):
            is_valid = False
            errors.append(f"SlotStartUnixS {self.SlotStartUnixS} must have type int.")
        if not isinstance(self.SlotDurationS, int):
            is_valid = False
            errors.append(f"Value {self.Value} must have type int.")
        if not isinstance(self.PowerWList, List):
            is_valid = False
            errors.append(f"PowerWList must be type list")
        

