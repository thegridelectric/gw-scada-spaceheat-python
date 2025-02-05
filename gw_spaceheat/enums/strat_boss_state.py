from enum import auto
from typing import List

from gw.enums import GwStrEnum

class StratBossState(GwStrEnum):
    Dormant = auto()  
    Active = auto()   

    @classmethod
    def enum_name(cls) -> str:
        return "strat.boss.state"

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]