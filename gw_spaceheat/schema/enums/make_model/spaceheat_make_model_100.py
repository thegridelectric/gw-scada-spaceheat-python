"""spaceheat.make.model.100 definition"""
import enum
from abc import ABC
from typing import List


class MakeModel(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    UNKNOWNMAKE__UNKNOWNMODEL = "UnknownMake__UnknownModel"
    EGAUGE__4030 = "Egauge__4030"
    NCD__PR814SPST = "NCD__PR8-14-SPST"
    ADAFRUIT__642 = "Adafruit__642"
    GRIDWORKS__TSNAP1 = "GridWorks__TSnap1"
    GRIDWORKS__WATERTEMPHIGHPRECISION = "GridWorks__WaterTempHighPrecision"
    GRIDWORKS__SIMPM1 = "Gridworks__SimPm1"
    SCHNEIDERELECTRIC__IEM3455 = "SchneiderElectric__Iem3455"
    GRIDWORKS__SIMBOOL30AMPRELAY = "GridWorks__SimBool30AmpRelay"
    OPENENERGY__EMONPI = "OpenEnergy__EmonPi"
    GRIDWORKS__SIMTSNAP1 = "Gridworks__SimTSnap1"

    #


class SpaceheatMakeModel100GtEnum(ABC):
    symbols: List[str] = [
        "00000000",
        "beb6d3fb",
        "fabfa505",
        "acd93fb3",
        "d0178dc3",
        "f8b497e8",
        "076da322",
        "d300635e",
        "e81d74a8",
        "c75d269f",
        "3042c432",

        #
    ]
