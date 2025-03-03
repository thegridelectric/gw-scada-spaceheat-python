from typing import Optional, Literal
from pydantic import BaseModel, model_validator
from enums import RepresentationStatus
from gwproto.property_format import LeftRightDotStr, UTCSeconds
from typing_extensions import Self

class SetRepresentationStatus(BaseModel):
    FromGNodeAlias: LeftRightDotStr
    TimeS: UTCSeconds
    Status: RepresentationStatus
    Reason: Optional[str]
    SignedProof: str = "algo_sig_dummy" # For blockchain validation
    TypeName: Literal["set.representation.status"] = "set.representation.status"
    Version: Literal["000"] = "000"


    @model_validator(mode='after')
    def check_axiom_1(self) -> Self:
        """
        SignedProof is signed by Atn holding TaTradingRights
        Future: Will validate Algorand smart contract transaction signature.

        sign({
            "FromGNodeAlias": "hw1.isone.keene.beech",
            "Status": "Active",
            "TimeS": 1740425972,
        })
        Currently accepts placeholder that follows basic Algorand message pack format.
        """
        # TODO: Replace with real Algorand transaction signature validation
        if not self.SignedProof.startswith("algo_sig_"):
            raise ValueError(
                "Even placeholder signatures must start with 'algo_sig_' "
                "to indicate Algorand signing intent"
            )
        return self