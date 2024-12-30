from typing import List, Literal
from pydantic import BaseModel, field_validator, model_validator


class AdminReleaseControl(BaseModel):
    TypeName: Literal["admin.release.control"] = "admin.release.control"
    Version: Literal["001"] = "001"