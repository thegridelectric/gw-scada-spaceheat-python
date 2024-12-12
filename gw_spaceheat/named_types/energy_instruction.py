"""Type energy.instruction, version 000"""

from typing import Literal

from gwproto.property_format import LeftRightDotStr, UTCMilliseconds, UTCSeconds
from pydantic import BaseModel, PositiveInt, field_validator


class EnergyInstruction(BaseModel):
    FromGNodeAlias: LeftRightDotStr
    SlotStartS: UTCSeconds
    SlotDurationMinutes: PositiveInt
    SendTimeMs: UTCMilliseconds
    AvgPowerWatts: PositiveInt
    TypeName: Literal["energy.instruction"] = "energy.instruction"
    Version: Literal["000"] = "000"

    @field_validator("SlotStartS")
    @classmethod
    def check_slot_start_s(cls, v: int) -> int:
        """
        Axiom 1: SlotStartS should fall on the top of. minutes
        """
        # Implement Axiom(s)
        return v
