"""Type heating.forecast, version 000"""

from typing import List, Literal

from gwproto.property_format import UTCSeconds
from pydantic import BaseModel, model_validator
from typing_extensions import Self


class HeatingForecast(BaseModel):
    Time: List[UTCSeconds]
    AvgPowerKw: List[float]
    RswtF: List[float]
    RswtDeltaTF: List[float]
    TypeName: Literal["heating.forecast"] = "heating.forecast"
    Version: Literal["000"] = "000"

    @model_validator(mode="after")
    def check_axiom_2(self) -> Self:
        """
        Axiom 2: Length of all the lists must be the same.

        """
        # Implement check for axiom 2"
        return self
