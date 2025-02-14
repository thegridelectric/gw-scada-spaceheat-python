from typing import Optional, Literal
from pydantic import BaseModel
from enums import RepresentationStatus

class SetRepresentationStatus(BaseModel):
    Status: RepresentationStatus
    Reason: Optional[str]
    TypeName: Literal["set.representation.status"] = "set.representation.status"
    Version: Literal["000"] = "000"