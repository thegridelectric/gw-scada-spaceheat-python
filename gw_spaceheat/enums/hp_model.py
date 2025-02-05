from enum import auto
from gw.enums import GwStrEnum

class HpModel(GwStrEnum):
    LgHighTempHydroKitPlusMultiV = auto()  
    SamsungHighTempHydroKitPlusMultiV= auto()   

    @classmethod
    def enum_name(cls) -> str:
        return "hp.model"
