from typing import List, Literal
from pydantic import BaseModel, field_validator, model_validator


class AdminKeepAlive(BaseModel):
    TypeName: Literal["admin.keepalive"] = "admin.keepalive"
    Version: Literal["001"] = "001"