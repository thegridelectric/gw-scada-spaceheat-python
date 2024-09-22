"""Type gt.sensor.reporting.config, version 100"""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, StrictInt

from gwproto.enums import TelemetryName, Unit

class GtSensorReportingConfig(BaseModel):
    TelemetryName: TelemetryName
    ReportingPeriodS: StrictInt
    SamplePeriodS: StrictInt
    ReportOnChange: bool
    Exponent: StrictInt
    Unit: Unit
    AsyncReportThreshold: Optional[float]
    TypeName: Literal["gt.sensor.reporting.config"] = "gt.sensor.reporting.config"
    Version: Literal["100"] = "100"

    model_config = ConfigDict(use_enum_values=True, extra="allow")