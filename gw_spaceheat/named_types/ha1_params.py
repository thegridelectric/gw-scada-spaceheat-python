"""Type ha1.params, version 001"""

from typing import Literal

from pydantic import BaseModel, StrictInt


class Ha1Params(BaseModel):
    AlphaTimes10: StrictInt
    BetaTimes100: StrictInt
    GammaEx6: StrictInt
    IntermediatePowerKw: float
    IntermediateRswtF: StrictInt
    DdPowerKw: float
    DdRswtF: StrictInt
    DdDeltaTF: StrictInt
    HpMaxKwTh: float
    MaxEwtF: StrictInt
    LoadOverestimationPercent: StrictInt
    TypeName: Literal["ha1.params"] = "ha1.params"
    Version: Literal["002"] = "002"
