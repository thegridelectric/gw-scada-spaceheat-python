"""Type energy.instruction, version 000"""

from typing import Literal

from gwproto.property_format import LeftRightDotStr, UTCMilliseconds, UTCSeconds
from pydantic import BaseModel, PositiveInt, StrictInt, field_validator, model_validator
from typing_extensions import Self


class RequestEnergyInstruction(BaseModel):
    TypeName: Literal["request.energy.instruction"] = "request.energy.instruction"
    Version: Literal["000"] = "000"