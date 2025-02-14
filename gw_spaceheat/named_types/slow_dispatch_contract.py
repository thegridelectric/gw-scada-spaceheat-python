from typing import Literal
import time
from pydantic import BaseModel, field_validator, PositiveInt
from gwproto.property_format import UUID4Str, UTCSeconds,  LeftRightDotStr

class SlowDispatchContract(BaseModel):
    """Represents a dispatch contract between Atn and Scada"""
    ScadaAlias: LeftRightDotStr
    StartS: UTCSeconds
    DurationMinutes: PositiveInt
    AvgPowerWatts: PositiveInt
    ContractId: UUID4Str
    TypeName: Literal["slow.dispatch.contract"] = "slow.dispatch.contract"
    Version: Literal["000"] = "000"

    @field_validator("StartS")
    @classmethod
    def check_start_s(cls, v: int) -> int:
        """
        Axiom 1: StartS should fall on the top of 5 minutes
        """
        if v % 300 != 0:
            raise ValueError(
                f"Axiom 1: SlotStartS should fall on the top of 5 minutes. But got {v % 300} seconds out"
            )
        return v

    
    
    def is_live(self) -> bool:
        now = time.time()
        return (now >= self.StartS and 
                now < self.StartS + self.DurationMinutes * 60)
