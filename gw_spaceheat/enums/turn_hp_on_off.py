from enum import auto
from gw.enums import GwStrEnum

class TurnHpOnOff(GwStrEnum):
    TurnOn = auto()  
    TurnOff = auto()   

    @classmethod
    def enum_name(cls) -> str:
        return "turn.hp.on.off"
