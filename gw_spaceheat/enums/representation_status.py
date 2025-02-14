from enum import auto
from typing import List

from gw.enums import GwStrEnum


class RepresentationStatus(GwStrEnum):
    """
    The possible states of a representation
    contract between Atn and Scada
    Values:
      - Ready  # Scada ready to receive a dispatch
      - Active # Currently operating under a live dispatch contract
      - Dormant  # Not accepting dispatch contracts

    For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#mainautostate)
    """

    Ready = auto()
    Active = auto()
    Dormant = auto()

    @classmethod
    def default(cls) -> "RepresentationStatus":
        return cls.Dormant

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]

    @classmethod
    def enum_name(cls) -> str:
        return "representation.status"

    @classmethod
    def enum_version(cls) -> str:
        return "000"
