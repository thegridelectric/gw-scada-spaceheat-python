"""Type admin.keep.alive, version 000"""

from typing import Literal

from pydantic import BaseModel


class AdminKeepAlive(BaseModel):
    """ """

    TypeName: Literal["admin.keep.alive"] = "admin.keep.alive"
    Version: Literal["000"] = "000"
