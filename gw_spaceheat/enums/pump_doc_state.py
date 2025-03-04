from enum import auto
from typing import List
from gw.enums import GwStrEnum

class PumpDocState(GwStrEnum):
    Dormant = auto()  
    Dist = auto() 
    Store = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "pump.doc.state"

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]