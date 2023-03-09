from abc import ABC
from enum import auto
from typing import Dict, List

from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError


class MakeModel(StrEnum):
    """
    Determines Make/Model of device associated to a Spaceheat Node supervised by SCADA.
    [More Info](https://gridworks-protocol.readthedocs.io/en/latest/make-model.html).

    Choices and descriptions:

      * UNKNOWNMAKE__UNKNOWNMODEL:
      * EGAUGE__4030: A power meter in Egauge's 403x line. [More Info](https://store.egauge.net/meters).
      * NCD__PR814SPST: NCD's 4-channel high-power relay controller + 4 GPIO with I2C interface. [More Info](https://store.ncd.io/product/4-channel-high-power-relay-controller-4-gpio-with-i2c-interface/?attribute_pa_choose-a-relay=20-amp-spdt).
      * ADAFRUIT__642: Adafruit's high-temp, water-proof 1-wire temp sensor. [More Info](https://www.adafruit.com/product/642).
      * GRIDWORKS__TSNAP1: Actual GridWorks TSnap 1.0 SCADA Box
      * GRIDWORKS__WATERTEMPHIGHPRECISION: Simulated temp sensor
      * GRIDWORKS__SIMPM1: Simulated power meter
      * SCHNEIDERELECTRIC__IEM3455: Schneider Electric IEM 344 utility meter
      * GRIDWORKS__SIMBOOL30AMPRELAY: Simulated relay
      * OPENENERGY__EMONPI: Open Energy's open source multipurpose sensing device (including internal power meter). [More Info](https://docs.openenergymonitor.org/emonpi/technical.html).
      * GRIDWORKS__SIMTSNAP1: Simulated SCADA Box
      * ATLAS__EZFLO: Atlas Scientific EZO Embedded Flow Meter Totalizer, pulse to I2C. [More Info](https://drive.google.com/drive/u/0/folders/142bBV1pQIbMpyIR_0iRUr5gnzWgknOJp).
      * MAGNELAB__SCT0300050: Magnelab 50A current transformer
      * YHDC__SCT013100: YHDC current transformer. [More Info](https://en.yhdc.com/product/SCT013-401.html).
    """

    UNKNOWNMAKE__UNKNOWNMODEL = auto()
    EGAUGE__4030 = auto()
    NCD__PR814SPST = auto()
    ADAFRUIT__642 = auto()
    GRIDWORKS__TSNAP1 = auto()
    GRIDWORKS__WATERTEMPHIGHPRECISION = auto()
    GRIDWORKS__SIMPM1 = auto()
    SCHNEIDERELECTRIC__IEM3455 = auto()
    GRIDWORKS__SIMBOOL30AMPRELAY = auto()
    OPENENERGY__EMONPI = auto()
    GRIDWORKS__SIMTSNAP1 = auto()
    ATLAS__EZFLO = auto()
    MAGNELAB__SCT0300050 = auto()
    YHDC__SCT013100 = auto()

    @classmethod
    def default(cls) -> "MakeModel":
        """
        Returns default value UNKNOWNMAKE__UNKNOWNMODEL
        """
        return cls.UNKNOWNMAKE__UNKNOWNMODEL

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]


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
        "d0b0e375",
        #
    ]


class MakeModelGtEnum(SpaceheatMakeModel100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class MakeModelMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not MakeModelGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {MakeModelMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, make_model):
        if not isinstance(make_model, MakeModel):
            raise MpSchemaError(f"{make_model} must be of type {MakeModel}")
        return cls.local_to_gt_dict[make_model]

    gt_to_local_dict: Dict[str, MakeModel] = {
        "00000000": MakeModel.UNKNOWNMAKE__UNKNOWNMODEL,
        "beb6d3fb": MakeModel.EGAUGE__4030,
        "fabfa505": MakeModel.NCD__PR814SPST,
        "acd93fb3": MakeModel.ADAFRUIT__642,
        "d0178dc3": MakeModel.GRIDWORKS__TSNAP1,
        "f8b497e8": MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION,
        "076da322": MakeModel.GRIDWORKS__SIMPM1,
        "d300635e": MakeModel.SCHNEIDERELECTRIC__IEM3455,
        "e81d74a8": MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY,
        "c75d269f": MakeModel.OPENENERGY__EMONPI,
        "3042c432": MakeModel.GRIDWORKS__SIMTSNAP1,
        "d0b0e375": MakeModel.ATLAS__EZFLO,
    }

    local_to_gt_dict: Dict[MakeModel, str] = {
        MakeModel.UNKNOWNMAKE__UNKNOWNMODEL: "00000000",
        MakeModel.EGAUGE__4030: "beb6d3fb",
        MakeModel.NCD__PR814SPST: "fabfa505",
        MakeModel.ADAFRUIT__642: "acd93fb3",
        MakeModel.GRIDWORKS__TSNAP1: "d0178dc3",
        MakeModel.GRIDWORKS__WATERTEMPHIGHPRECISION: "f8b497e8",
        MakeModel.GRIDWORKS__SIMPM1: "076da322",
        MakeModel.SCHNEIDERELECTRIC__IEM3455: "d300635e",
        MakeModel.GRIDWORKS__SIMBOOL30AMPRELAY: "e81d74a8",
        MakeModel.OPENENERGY__EMONPI: "c75d269f",
        MakeModel.GRIDWORKS__SIMTSNAP1: "3042c432",
        MakeModel.ATLAS__EZFLO: "d0b0e375",
        #
    }
