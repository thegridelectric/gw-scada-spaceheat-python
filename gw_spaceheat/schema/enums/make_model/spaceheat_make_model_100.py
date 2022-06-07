"""spaceheat.make.model.100 definition"""
from abc import ABC
import enum
from typing import List


class MakeModel(enum.Enum):
    GRIDWORKS__WATERTEMPHIGHPRECISION = "GridWorks__WaterTempHighPrecision"
    GRIDWORKS__SIMBOOL30AMPRELAY = "GridWorks__SimBool30AmpRelay"
    ADAFRUIT__642 = "Adafruit__642"
    NCD__PR814SPST = "NCD__PR8-14-SPST"
    UNKNOWNMAKE__UNKNOWNMODEL = "UnknownMake__UnknownModel"
    

class SpaceheatMakeModel100GtEnum(ABC):
    symbols: List[str] = ["f8b497e8",
                          "e81d74a8",
                          "acd93fb3",
                          "fabfa505",
                          "b6a32d9b",
                          ]
