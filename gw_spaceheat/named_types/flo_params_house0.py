"""Type flo.params.house0, version 000"""
import uuid
import time
from typing import List, Literal, Optional

from gwproto.property_format import LeftRightDotStr, UTCSeconds, UUID4Str
from pydantic import BaseModel, PositiveInt, StrictInt, Field

from enums import MarketPriceUnit

class FloParamsHouse0(BaseModel):
    GNodeAlias: LeftRightDotStr
    FloParamsUid: UUID4Str = Field(default_factory=lambda: str(uuid.uuid4()))
    TimezoneStr: str = "America/New_York"
    StartUnixS: UTCSeconds
    HorizonHours: PositiveInt = 48
    NumLayers: PositiveInt = 24
    # Equipment
    StorageVolumeGallons: PositiveInt = 360
    StorageLossesPercent: float = 0.5
    HpMinElecKw: float = -0.5
    HpMaxElecKw: float = 11
    CopIntercept: float = 1.8
    CopOatCoeff: float = 0
    CopLwtCoeff: float = 0
    # Initial state
    InitialTopTempF: StrictInt 
    InitialThermocline: StrictInt
    # Forecasts
    LmpForecast: Optional[List[float]] = None
    DistPriceForecast: Optional[List[float]] = None
    RegPriceForecast: Optional[List[float]] = None
    PriceForecastUid: UUID4Str = Field(default_factory=lambda: str(uuid.uuid4()))
    OatForecastF: Optional[List[float]] = None
    WindSpeedForecastMph: Optional[List[float]] = None
    WeatherUid: UUID4Str = Field(default_factory=lambda: str(uuid.uuid4()))
    # House parameters
    AlphaTimes10: StrictInt
    BetaTimes100: StrictInt
    GammaEx6: StrictInt
    IntermediatePowerKw: float
    IntermediateRswtF: StrictInt
    DdPowerKw: float
    DdRswtF: StrictInt
    DdDeltaTF: StrictInt
    MaxEwtF: StrictInt
    PriceUnit: MarketPriceUnit = MarketPriceUnit.USDPerMWh
    ParamsGeneratedS: UTCSeconds = Field(default_factory=lambda: int(time.time()))
    TypeName: Literal["flo.params.house0"] = "flo.params.house0"
    Version: Literal["000"] = "000"
