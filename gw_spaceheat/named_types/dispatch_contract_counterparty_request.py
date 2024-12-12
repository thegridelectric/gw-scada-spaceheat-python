"""Type dispatch.contract.counterparty.request, version 000"""

from typing import Literal

from gwproto.property_format import LeftRightDotStr
from pydantic import BaseModel


class DispatchContractCounterpartyRequest(BaseModel):
    """
    Triggers AtnWantsControl.

    Sent by the Atn to its SCADA when they share an existing DispatchContract. If the SCADA
    is in HomeAlone and gets this message, it will move into Atn mode.
    """

    FromGNodeAlias: LeftRightDotStr
    BlockchainSig: str
    TypeName: Literal[
        "dispatch.contract.counterparty.request"
    ] = "dispatch.contract.counterparty.request"
    Version: Literal["000"] = "000"

