"""Type game.on, version 000"""
import time
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from gwproto.property_format import LeftRightDotStr, UTCMilliseconds

class GameOn(BaseModel):
    """
    Sent from Scada to Atn indicating Dispatch Contract is live
    """
    FromGNodeAlias: LeftRightDotStr
    SendTimeMs: UTCMilliseconds = Field(default_factory=lambda: int(time.time() * 1000))
    DispatchContractAddress: str = "bogus Algo Smart Contract Address"
    Signature: str = "bogus Algo signature"
    TypeName: Literal["game.on"] = "game.on"
    Version: Literal["000"] = "000"

    @field_validator("DispatchContractAddress")
    @classmethod
    def _check_dispatch_contract_address(cls, v: str) -> str:
        # try:
        #     check_is_algo_address(v)
        # except ValueError as e:
        #     raise ValueError(
        #         f"DispatchContractAddress failed AlgoAddress format validation: {e}",
        #     ) from e
        return v

    @field_validator("Signature")
    @classmethod
    def _check_signature(cls, v: str) -> str:
        # try:
        #     check_is_algo_msg_pack_encoded(v)
        # except ValueError as e:
        #     raise ValueError(
        #         f"Signature failed AlgoMsgPackEncoded format validation: {e}",
        #     ) from e
        return v
