from typing import Literal, List
from pydantic import BaseModel
from datetime import datetime

class HeatingForecast(BaseModel):
    Time: List[datetime]
    AvgPower: List[float]
    Rswt: List[float]
    RswtDeltaT: List[float]
    TypeName: Literal["heating.forecast"] = "heating.forecast"
    Version: Literal["000"] = "000"