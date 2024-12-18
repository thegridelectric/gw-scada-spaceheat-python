"""Type flo.params.house0, version 000"""

from typing import List, Literal, Optional

from gwproto.property_format import LeftRightDotStr, UTCSeconds, UUID4Str
from pydantic import BaseModel, PositiveInt, StrictInt

from enums import MarketPriceUnit

class FloParamsHouse0(BaseModel):
    GNodeAlias: LeftRightDotStr
    FloParamsUid: UUID4Str
    TimezoneStr: str
    StartUnixS: UTCSeconds
    HorizonHours: PositiveInt
    StorageVolumeGallons: PositiveInt
    StorageLossesPercent: float
    HpMinElecKw: float
    HpMaxElecKw: float
    CopIntercept: float
    CopOatCoeff: float
    CopLwtCoeff: float
    InitialTopTempF: StrictInt
    InitialThermocline: StrictInt
    LmpForecast: Optional[List[float]] = None
    DistPriceForecast: Optional[List[float]] = None
    RegPriceForecast: Optional[List[float]] = None
    PriceForecastUid: UUID4Str
    OatForecastF: Optional[List[float]] = None
    WindSpeedForecastMph: Optional[List[float]] = None
    WeatherUid: UUID4Str
    AlphaTimes10: StrictInt
    BetaTimes100: StrictInt
    GammaEx6: StrictInt
    IntermediatePowerKw: float
    IntermediateRswtF: StrictInt
    DdPowerKw: float
    DdRswtF: StrictInt
    DdDeltaTF: StrictInt
    MaxEwtF: StrictInt
    MarketPriceUnit: MarketPriceUnit
    ParamsGeneratedS: UTCSeconds
    TypeName: Literal["flo.params.house0"] = "flo.params.house0"
    Version: Literal["000"] = "000"
