"""Type go.dormant, version 000"""

from typing import Literal
from uuid import uuid4

from gwproto.property_format import SpaceheatName, UUID4Str
from pydantic import BaseModel, Field


class GoDormant(BaseModel):
    FromName: SpaceheatName
    ToName: SpaceheatName
    TriggerId: UUID4Str = Field(default_factory=lambda: str(uuid4()))
    TypeName: Literal["go.dormant"] = "go.dormant"
    Version: Literal["000"] = "000"
