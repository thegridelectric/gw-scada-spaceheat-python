"""Base for gt.sensor.reporting.config"""
import json
from typing import List, Optional, NamedTuple
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtSensorReportingConfigBase(NamedTuple):
    Exponent: int     #
    ReportOnChange: bool     #
    IsExact: bool     #
    MaxExpectedValue: int     #
    ChangeThresholdOfMax: float     #
    CheckingPeriodMs: int     #
    MinExpectedValue: int     #
    CheckAsFastAsPossible: bool     #
    ReportingPeriodMs: int     #
    TelemetryName: TelemetryName     #
    TypeAlias: str = 'gt.sensor.reporting.config.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        del(d["TelemetryName"])
        d["SpaceheatTelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.Exponent, int):
            errors.append(f"Exponent {self.Exponent} must have type int.")
        if not isinstance(self.ReportOnChange, bool):
            errors.append(f"ReportOnChange {self.ReportOnChange} must have type bool.")
        if not isinstance(self.IsExact, bool):
            errors.append(f"IsExact {self.IsExact} must have type bool.")
        if not isinstance(self.MaxExpectedValue, int):
            errors.append(f"MaxExpectedValue {self.MaxExpectedValue} must have type int.")
        if not isinstance(self.ChangeThresholdOfMax, float):
            errors.append(f"ChangeThresholdOfMax {self.ChangeThresholdOfMax} must have type float.")
        if not isinstance(self.CheckingPeriodMs, int):
            errors.append(f"CheckingPeriodMs {self.CheckingPeriodMs} must have type int.")
        if not isinstance(self.MinExpectedValue, int):
            errors.append(f"MinExpectedValue {self.MinExpectedValue} must have type int.")
        if not isinstance(self.CheckAsFastAsPossible, bool):
            errors.append(f"CheckAsFastAsPossible {self.CheckAsFastAsPossible} must have type bool.")
        if not isinstance(self.ReportingPeriodMs, int):
            errors.append(f"ReportingPeriodMs {self.ReportingPeriodMs} must have type int.")
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(f"TelemetryName {self.TelemetryName} must have type {TelemetryName}.")
        if self.TypeAlias != 'gt.sensor.reporting.config.100':
            errors.append(f"Type requires TypeAlias of gt.sensor.reporting.config.100, not {self.TypeAlias}.")
        
        return errors
