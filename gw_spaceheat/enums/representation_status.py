from enum import auto
from typing import List

from gw.enums import GwStrEnum


class RepresentationStatus(GwStrEnum):
    """
    Representation Status handles intentional availability/unavailability
    Values:
      - Active # Atn can attempt to establish a contract
      - Dormant  # Atn should not try to establish a contract - Scada
      is intentionally not accepting them

    For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#mainautostate)
    """

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
