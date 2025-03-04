from enum import auto
from typing import List
from gw.enums import GwStrEnum

class PumpDocEvent(GwStrEnum):
    Timeout = auto()  # Dist/Primary/Store -> Dormant
    NoDistFlow = auto() # Dormant -> Dist
    NoStoreFlow = auto() # Dormant -> Store

    @classmethod
    def enum_name(cls) -> str:
        return "pump.doc.event"

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]