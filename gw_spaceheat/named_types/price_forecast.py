from typing import Literal, List
from pydantic import BaseModel
from datetime import datetime

class PriceForecast(BaseModel):
    DpForecast: List[float]
    LmpForecsat: List[float]
    TypeName: Literal["price.forecast"] = "price.forecast"
    Version: Literal["000"] = "000"