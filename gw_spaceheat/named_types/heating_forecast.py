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
    def check_axiom_1(self) -> Self:
        """
        Axiom 1: Length of all the lists must be the same.

        """
        if len(self.AvgPowerKw) != len(self.Time):
            raise ValueError(
                f"self.AvgPowerKw should be a list of length {len(self.Time)}!"
            )
        if len(self.RswtF) != len(self.Time):
            raise ValueError(f"self.RswtF should be a list of length {len(self.Time)}!")
        if len(self.RswtDeltaTF) != len(self.Time):
            raise ValueError(
                f"self.RswtDeltaTFshould be a list of length {len(self.Time)}!"
            )
        return self
