"""spaceheat.make.model.100 definition"""
import enum
from abc import ABC
from typing import List


class MakeModel(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    GRIDWORKS__WATERTEMPHIGHPRECISION = "GridWorks__WaterTempHighPrecision"
    GRIDWORKS__SIMPM1 = "Gridworks__SimPm1"
    SCHNEIDERELECTRIC__IEM3455 = "SchneiderElectric__Iem3455"
    GRIDWORKS__SIMBOOL30AMPRELAY = "GridWorks__SimBool30AmpRelay"
    ADAFRUIT__642 = "Adafruit__642"
    NCD__PR814SPST = "NCD__PR8-14-SPST"
    UNKNOWNMAKE__UNKNOWNMODEL = "UnknownMake__UnknownModel"
    OPENENERGY__EMONPI = "OpenEnergy__EmonPi"
    G1__NCD_ADS1115__TEWA_NTC_10K_A = "G1__NcdAds1115__TewaNtc10kA"
    G1__NCD_ADS1115__AMPH_NTC_10K_A = "G1__NcdAds1115__AmphNtc10kA"

    #


class SpaceheatMakeModel100GtEnum(ABC):
    symbols: List[str] = [
        "f8b497e8",
        "076da322",
        "d300635e",
        "e81d74a8",
        "acd93fb3",
        "fabfa505",
        "00000000",
        "c75d269f",
        "e3364590",
        "90566a90",

        #
    ]
