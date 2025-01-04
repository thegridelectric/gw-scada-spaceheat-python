import uuid
from typing import Literal

from gwproto.property_format import LeftRightDotStr, UUID4Str
from pydantic import BaseModel, Field


class ScadaInit(BaseModel):
    FromGNodeAlias: LeftRightDotStr
    MessageId: UUID4Str = Field(default_factory=lambda: str(uuid.uuid4()))
    TypeName: Literal["scada.init"] = "scada.init"
    Version: Literal["000"] = "000"