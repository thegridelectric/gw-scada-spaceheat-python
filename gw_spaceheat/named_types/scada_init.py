import uuid
from typing import Literal
from pydantic import BaseModel, Field
from gwproto.property_format import LeftRightDotStr, UUID4Str

class ScadaInit(BaseModel):
    FromGNodeAlias: LeftRightDotStr
    MessageId: UUID4Str = Field(default_factory=lambda: str(uuid.uuid4()))
    TypeName: Literal["scada.init"] = "scada.init"
    Version: Literal["000"] = "000"