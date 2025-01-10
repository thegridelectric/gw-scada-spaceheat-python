from enum import auto
from typing import List

from gw.enums import GwStrEnum


class HomeAloneTopState(GwStrEnum):
    """
    
    Values:
      - Dormant
      - Normal
      - UsingBackupOnpeak
      - ScadaBlind

    For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#homealonetopstate)
    """

    Dormant = auto()
    Normal = auto()
    UsingBackupOnpeak = auto()
    ScadaBlind = auto()

    @classmethod
    def default(cls) -> "HomeAloneTopState":
        return cls.Normal

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]

    @classmethod
    def enum_name(cls) -> str:
        return "home.alone.top.state"

    @classmethod
    def enum_version(cls) -> str:
        return "000"
