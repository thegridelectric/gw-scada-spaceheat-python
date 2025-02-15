
from typing import Optional, Literal
from gwproto.property_format import  UTCMilliseconds, SpaceheatName
from pydantic import BaseModel, field_validator, model_validator
from enums import ContractStatus
from named_types import SlowDispatchContract
from typing_extensions import Self

class SlowContractHeartbeat(BaseModel):
    """Base class for contract lifecycle messages"""
    FromNode: SpaceheatName # either "a" or "s", for Atn or Scada
    Contract: SlowDispatchContract
    PreviousStatus: Optional[ContractStatus] = None
    Status: ContractStatus
    MessageCreatedMs: UTCMilliseconds  
    Cause: Optional[str] = None
    IsAuthoritative: bool = True
    MyDigit: int
    YourLastDigit: Optional[int]
    SignedProof: str = "algo_sig_dummy" # For blockchain validation
    TypeName: Literal["slow.contract.heartbeat"] = "slow.contract.heartbeat"
    Version: Literal["000"] = "000"

    @model_validator(mode="after")
    def _check_axiom_1(self) -> Self:
        """Axiom 1: Contracts  created no later than 10 seconds after StartS"""
        if self.Status == ContractStatus.Created:
            time_s = self.MessageCreatedMs / 1000
            if time_s > self.Contract.StartS + 10:
                raise ValueError(
                    f"Axiom 2: Must be created within 10 seconds of Contract Start. Got {round(time_s - self.Contract.StartS, 2)}"
                )
        return self
    
    @model_validator(mode='after')
    def _check_axiom_2(self) -> Self:
        """Axiom 2 Check authority: Validate authority for status changes"""
        
        # Only Atn can create or confirm
        if self.Status in [ContractStatus.Created, ContractStatus.Confirmed]:
            if self.FromNode != "a":
                raise ValueError(f"Only Atn can set status {self.Status}")
            if not self.IsAuthoritative:
                raise ValueError("Atn IsAuthoritative for Created and Confirmed!")
        # Only Scada can mark as received
        if self.Status == ContractStatus.Received:
            if self.FromNode != "s":
                raise ValueError("Only Scada can set Received status")
            if not self.IsAuthoritative:
                raise ValueError("Scada IsAuthoritative for Received!")
        # Active/CompletedSuccess/CompletedFailure are for umpire only
        # For now, treat these as claims by participants
        if self.Status in [ContractStatus.Active, 
                          ContractStatus.CompletedSuccess,
                          ContractStatus.CompletedFailure]:
            # Later the umpire will enforce these
            # For now just let participants publish their view
            if self.IsAuthoritative:
                raise ValueError(f"{self.FromNode} is NOT Authoritative for {self.Status}")

        return self

    @model_validator(mode='after')
    def check_axiom_3(self) -> Self:
        """Axiom 3: Cause required for and limited to Terminated and CompletedFailure"""
        needs_cause = self.Status in [ContractStatus.Terminated, ContractStatus.CompletedFailure]
        has_cause = self.Cause is not None

        if needs_cause and not has_cause:
            raise ValueError("Cause is required for Terminated and CompletedFailure status")
        if not needs_cause and has_cause:
            raise ValueError("Cause only valid for Terminated and CompletedFailure status")
        return self

    @model_validator(mode='after')
    def check_axiom_4(self) -> Self:
        """Axiom 3: Cause required for and limited to Terminated and CompletedFailure"""
        needs_cause = self.Status in [ContractStatus.Terminated, ContractStatus.CompletedFailure]
        has_cause = self.Cause is not None

        if needs_cause and not has_cause:
            raise ValueError("Cause is required for Terminated and CompletedFailure status")
        if not needs_cause and has_cause:
            raise ValueError("Cause only valid for Terminated and CompletedFailure status")
        return self

    @field_validator("FromNode")
    @classmethod
    def _check_from_node(cls, v: str) -> str:
        """
        Axiom 5: FromNode should be 's' (Scada) or 'a' (AtomicTNode)
        """
        if v not in ['s', 'a']:
            raise ValueError(
                f"Axiom 4: FromNode should be 's' (Scada) or 'a' (AtomicTNode). Got {v}"
            )
        return v

    @model_validator(mode='after')
    def check_axiom_6(self) -> Self:
        """
        Future: Will validate Algorand smart contract transaction signature.

        By including YourLastDigit and the previous message's SignedProof,
        this creates an unbreakable chain where:
          - Each party must reference the exact signature from their counterparty's last message
          - The digits create a crosslinked sequence that must match on both sides
          - The signatures create a cryptographic chain that can't be spoofed by one side after-the-fact
        sign({
            "ContractId": "c3cd6c8d-e8d8-4875-8f7b-d3ea13c28693", 
            "FromNode": "a",
            "Status": "Active",
            "MessageCreatedMs": 1234567890,
            "MyDigit": 3,
            "YourLastDigit": 7,
            "PrevSignedProof": "algo_sig_xyz..."
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

    @model_validator(mode='after')
    def check_axiom_7(self) -> Self:
        """Axiom 7: check digits"""
        if self.MyDigit not in range(10):
            raise ValueError(f"MyDigit must be in range(10) not {self.MyDigit}")
        if self.YourLastDigit:
            if self.YourLastDigit not in range(10):
                raise ValueError(f"YourLastDigit must be in range(10) not {self.YourLastDigit}")
        return self




