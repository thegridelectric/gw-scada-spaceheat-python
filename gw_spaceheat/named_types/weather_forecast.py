"""Type weather.forecast, version 000"""
import uuid
import time
from typing import List, Literal

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self
from gwproto.property_format import (
    HandleName, LeftRightDotStr, UUID4Str, UTCSeconds
)

class WeatherForecast(BaseModel):
    """
    Weather Forecast Raw.

    A type meant to be used for weather forecast data from a direct third-party source.
    """
    FromGNodeAlias: LeftRightDotStr
    WeatherChannelName: HandleName
    Time: List[UTCSeconds]
    OatF: List[float]
    WindSpeedMph: List[float]
    WeatherUid: UUID4Str = Field(default_factory=lambda: str(uuid.uuid4(())))
    ForecastCreatedS: UTCSeconds = Field(default_factory=lambda: int(time.time()))
    TypeName: Literal["weather.forecast"] = "weather.forecast"
    Version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Length of all the lists (Time, OatF, WindspeedMph) must be the same.

        """
        # Implement check for axiom 1"
        return self
