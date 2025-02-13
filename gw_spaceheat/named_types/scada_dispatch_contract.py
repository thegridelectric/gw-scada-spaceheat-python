from typing import Literal
import time
from pydantic import BaseModel, model_validator, PositiveInt
from typing_extensions import Self
from gw.enums import MarketTypeName
from gwproto.property_format import UUID4Str, UTCSeconds, LeftRightDotStr, 

class ScadaDispatchContract(BaseModel):
    """Represents an active dispatch contract between Atn and Scada"""
    ContractId: UUID4Str
    ScadaAlias: LeftRightDotStr
    SlotStartS: UTCSeconds
    DurationMinutes: PositiveInt
    DurationMinutes: int
    AvgPowerWatts: int
    Signature: str
    Status: Literal["Pending", "Active", "Completed", "Failed"]
    TypeName: Literal["dispatch.contract"] = "dispatch.contract"
    Version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1:  MarketSlotName, StartUnixS, DurationMinutes are all consistent
        """
        # Implement check for axiom 1"
        return self
    
    def is_live(self) -> bool:
        now = time.time()
        return (now >= self.StartUnixS and 
                now < self.StartUnixS + self.DurationMinutes * 60)

    @property
    def market_type_name(self) -> MarketTypeName:
        """Extract MarketTypeName from MarketSlotName"""
        return MarketTypeName(self.MarketSlotName.split('.')[1])