from enum import auto
from gw.enums import GwStrEnum

class MainAutoState(GwStrEnum):
    Atn = auto()
    HomeAlone = auto()
    Dormant = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "main.auto.state"

class MainAutoEvent(GwStrEnum):
    AtnLinkDead = auto()
    AtnDispatchRequest = auto()
    GoDormant = auto()
    WakeUp = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "main.auto.event"
    
class TopState(GwStrEnum):
    Auto = auto()
    Admin = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "top.state"

class TopEvent(GwStrEnum):
    AdminWakesUp = auto()
    AdminTimesOut= auto()

    @classmethod
    def enum_name(cls) -> str:
        return "top.event"