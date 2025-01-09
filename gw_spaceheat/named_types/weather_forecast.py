from typing import Literal, List
from pydantic import BaseModel
from gwproto.property_format import UTCSeconds

class WeatherForecast(BaseModel):
    Time: List[UTCSeconds]
    OatF: List[float]
    WindSpeedMph: List[float]
    TypeName: Literal["weather.forecast"] = "weather.forecast"
    Version: Literal["001"] = "001"