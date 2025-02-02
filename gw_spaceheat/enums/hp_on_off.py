from enum import auto
from gw.enums import GwStrEnum

class HpOnOff(GwStrEnum):
    TurnOn = auto()  
    TurnOff = auto()   

    @classmethod
    def enum_name(cls) -> str:
        return "hp.on.off"
