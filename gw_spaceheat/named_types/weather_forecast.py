from typing import Literal, List
from pydantic import BaseModel
from datetime import datetime

class WeatherForecast(BaseModel):
    Time: List[datetime]
    Oat: List[float]
    WindSpeed: List[float]
    TypeName: Literal["weather.forecast"] = "weather.forecast"
    Version: Literal["001"] = "001"