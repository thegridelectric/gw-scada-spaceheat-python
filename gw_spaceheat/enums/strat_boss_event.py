from enum import auto
from typing import List

from gw.enums import GwStrEnum

class StratBossEvent(GwStrEnum):
    HpTurnOnReceived = auto()  
    DefrostDetected = auto() 
    LiftDetected = auto()
    HpTurnOffReceived = auto() 
    Timeout = auto()
    BossCancels = auto()
     
    @classmethod
    def enum_name(cls) -> str:
        return "strat.boss.event"
    
    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]