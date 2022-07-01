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
    #


class SpaceheatMakeModel100GtEnum(ABC):
    symbols: List[str] = [
        "f8b497e8",
        "076da322",
        "d300635e",
        "e81d74a8",
        "acd93fb3",
        "fabfa505",
        "b6a32d9b",
        #
    ]
