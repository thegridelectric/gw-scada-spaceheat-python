"""Base for gt.sensor.reporting.config"""
import json
from typing import List, Optional, NamedTuple
import schema.property_format as property_format
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap
from schema.enums.units.units_map import Units, UnitsMap


class GtSensorReportingConfigBase(NamedTuple):
    ReportOnChange: bool     #
    Exponent: int     #
    ScalingFactor: int     #
    ReportingPeriodS: int     #
    SamplePeriodS: int     #
    TelemetryName: TelemetryName     #
    Units: Units     #
    AsyncReportThreshold: Optional[float] = None
    TypeAlias: str = 'gt.sensor.reporting.config.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["AsyncReportThreshold"] is None:
            del d["AsyncReportThreshold"]
        del(d["TelemetryName"])
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        del(d["Units"])
        d["UnitsGtEnumSymbol"] = UnitsMap.local_to_gt(self.Units)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ReportOnChange, bool):
            errors.append(f"ReportOnChange {self.ReportOnChange} must have type bool.")
        if self.AsyncReportThreshold:
            if not isinstance(self.AsyncReportThreshold, float):
                errors.append(f"AsyncReportThreshold {self.AsyncReportThreshold} must have type float.")
        if not isinstance(self.Exponent, int):
            errors.append(f"Exponent {self.Exponent} must have type int.")
        if not isinstance(self.ScalingFactor, int):
            errors.append(f"ScalingFactor {self.ScalingFactor} must have type int.")
        if not isinstance(self.ReportingPeriodS, int):
            errors.append(f"ReportingPeriodS {self.ReportingPeriodS} must have type int.")
        if not isinstance(self.SamplePeriodS, int):
            errors.append(f"SamplePeriodS {self.SamplePeriodS} must have type int.")
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(f"TelemetryName {self.TelemetryName} must have type {TelemetryName}.")
        if not isinstance(self.Units, Units):
            errors.append(f"Units {self.Units} must have type {Units}.")
        if self.TypeAlias != 'gt.sensor.reporting.config.100':
            errors.append(f"Type requires TypeAlias of gt.sensor.reporting.config.100, not {self.TypeAlias}.")
        
        return errors
