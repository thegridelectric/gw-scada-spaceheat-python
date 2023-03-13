""" Enum with TypeName spaceheat.make.model, Version 000"""
from enum import auto
from typing import List

from fastapi_utils.enums import StrEnum


class MakeModel(StrEnum):
    """
    Determines Make/Model of device associated to a Spaceheat Node supervised by SCADA
    [More Info](https://gridworks-protocol.readthedocs.io/en/latest/make-model.html).

    Name (EnumSymbol, Version): description

      * UNKNOWNMAKE__UNKNOWNMODEL (00000000, 000):
      * EGAUGE__4030 (beb6d3fb, 000): A power meter in Egauge's 403x line. [More Info](https://store.egauge.net/meters).
      * NCD__PR814SPST (fabfa505, 000): NCD's 4-channel high-power relay controller + 4 GPIO with I2C interface. [More Info](https://store.ncd.io/product/4-channel-high-power-relay-controller-4-gpio-with-i2c-interface/?attribute_pa_choose-a-relay=20-amp-spdt).
      * ADAFRUIT__642 (acd93fb3, 000): Adafruit's high-temp, water-proof 1-wire temp sensor. [More Info](https://www.adafruit.com/product/642).
      * GRIDWORKS__TSNAP1 (d0178dc3, 000): Actual GridWorks TSnap 1.0 SCADA Box
      * GRIDWORKS__WATERTEMPHIGHPRECISION (f8b497e8, 000): Simulated temp sensor
      * GRIDWORKS__SIMPM1 (076da322, 000): Simulated power meter
      * SCHNEIDERELECTRIC__IEM3455 (d300635e, 000): Schneider Electric IEM 344 utility meter
      * GRIDWORKS__SIMBOOL30AMPRELAY (e81d74a8, 000): Simulated relay
      * OPENENERGY__EMONPI (c75d269f, 000): Open Energy's open source multipurpose sensing device (including internal power meter). [More Info](https://docs.openenergymonitor.org/emonpi/technical.html).
      * GRIDWORKS__SIMTSNAP1 (3042c432, 000): Simulated SCADA Box
      * ATLAS__EZFLO (d0b0e375, 000): Atlas Scientific EZO Embedded Flow Meter Totalizer, pulse to I2C. [More Info](https://drive.google.com/drive/u/0/folders/142bBV1pQIbMpyIR_0iRUr5gnzWgknOJp).
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
