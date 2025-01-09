from typing import Literal, List
from pydantic import BaseModel
from gwproto.property_format import UTCSeconds

class HeatingForecast(BaseModel):
    Time: List[UTCSeconds]
    AvgPowerKw: List[float]
    RswtF: List[float]
    RswtDeltaTF: List[float]
    TypeName: Literal["heating.forecast"] = "heating.forecast"
    Version: Literal["000"] = "000"