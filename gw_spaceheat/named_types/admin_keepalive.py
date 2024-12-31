from typing import Optional, Literal
from pydantic import BaseModel, field_validator, model_validator


class AdminKeepAlive(BaseModel):
    AdminTimeoutSeconds: Optional[int] = None
    TypeName: Literal["admin.keepalive"] = "admin.keepalive"
    Version: Literal["001"] = "001"