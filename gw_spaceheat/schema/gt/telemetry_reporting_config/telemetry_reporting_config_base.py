"""Base for telemetry.reporting.config.000"""
import json
from typing import List, NamedTuple, Optional
import schema.property_format as property_format
from enums import (
    Unit,
    UnitMap,
)
from enums import (
    TelemetryName,
    TelemetryNameMap,
)


class TelemetryReportingConfigBase(NamedTuple):
    ReportOnChange: bool  #
    Exponent: int  #
    Unit: Unit  #
    AboutNodeName: str  #
    SamplePeriodS: int  #
    TelemetryName: TelemetryName  #
    AsyncReportThreshold: Optional[float] = None
    NameplateMaxValue: Optional[int] = None
    TypeAlias: str = "telemetry.reporting.config.000"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del d["Unit"]
        d["UnitGtEnumSymbol"] = UnitMap.local_to_gt(self.Unit)
        if d["AsyncReportThreshold"] is None:
            del d["AsyncReportThreshold"]
        if d["NameplateMaxValue"] is None:
            del d["NameplateMaxValue"]
        del d["TelemetryName"]
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ReportOnChange, bool):
            errors.append(
                f"ReportOnChange {self.ReportOnChange} must have type bool."
            )
        if not isinstance(self.Exponent, int):
            errors.append(
                f"Exponent {self.Exponent} must have type int."
            )
        if not isinstance(self.Unit, Unit):
            errors.append(
                f"Unit {self.Unit} must have type {Unit}."
            )
        if not isinstance(self.AboutNodeName, str):
            errors.append(
                f"AboutNodeName {self.AboutNodeName} must have type str."
            )
        if not property_format.is_lrd_alias_format(self.AboutNodeName):
            errors.append(
                f"AboutNodeName {self.AboutNodeName}"
                " must have format LrdAliasFormat"
            )
        if self.AsyncReportThreshold:
            if not isinstance(self.AsyncReportThreshold, float):
                errors.append(
                    f"AsyncReportThreshold {self.AsyncReportThreshold} must have type float."
                )
        if self.NameplateMaxValue:
            if not isinstance(self.NameplateMaxValue, int):
                errors.append(
                    f"NameplateMaxValue {self.NameplateMaxValue} must have type int."
                )
        if not isinstance(self.SamplePeriodS, int):
            errors.append(
                f"SamplePeriodS {self.SamplePeriodS} must have type int."
            )
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(
                f"TelemetryName {self.TelemetryName} must have type {TelemetryName}."
            )
        if self.TypeAlias != "telemetry.reporting.config.000":
            errors.append(
                f"Type requires TypeAlias of telemetry.reporting.config.000, not {self.TypeAlias}."
            )

        return errors
