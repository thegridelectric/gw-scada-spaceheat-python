"""Type ally.gives.up, version 000"""

from typing import Literal

from gwproto.property_format import SpaceheatName
from pydantic import BaseModel


class AllyGivesUp(BaseModel):
    FromName: SpaceheatName
    ToName: SpaceheatName
    Reason: str  # This allows us to communicate why we're giving up
    TypeName: Literal["ally.gives.up"] = "ally.gives.up"
    Version: Literal["000"] = "000"