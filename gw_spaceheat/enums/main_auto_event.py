from enum import auto
from typing import List

from gw.enums import GwStrEnum


class MainAutoEvent(GwStrEnum):
    """
    
    Values:
      - AtnLinkDead
      - AtnWantsControl
      - AutoGoesDormant
      - AutoWakesUp

    For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#mainautoevent)
    """

    AtnLinkDead = auto()
    AtnWantsControl = auto()
    AutoGoesDormant = auto()
    AutoWakesUp = auto()

    @classmethod
    def default(cls) -> "MainAutoEvent":
        return cls.AutoGoesDormant

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]

    @classmethod
    def enum_name(cls) -> str:
        return "main.auto.event"

    @classmethod
    def enum_version(cls) -> str:
        return "000"
