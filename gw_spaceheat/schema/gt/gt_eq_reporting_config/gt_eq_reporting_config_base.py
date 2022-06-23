"""Base for gt.eq.reporting.config.100"""
import json
from typing import List, Optional, NamedTuple
from schema.enums.unit.unit_map import Unit, UnitMap
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtEqReportingConfigBase(NamedTuple):
    ReportOnChange: bool     #
    Exponent: int     #
    SamplePeriodS: int     #
    Unit: Unit     #
    TelemetryName: TelemetryName     #
    AsyncReportThreshold: Optional[float] = None
    TypeAlias: str = 'gt.eq.reporting.config.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["AsyncReportThreshold"] is None:
            del d["AsyncReportThreshold"]
        del(d["Unit"])
        d["UnitGtEnumSymbol"] = UnitMap.local_to_gt(self.Unit)
        del(d["TelemetryName"])
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_gt(self.TelemetryName)
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ReportOnChange, bool):
            errors.append(f"ReportOnChange {self.ReportOnChange} must have type bool.")
        if not isinstance(self.Exponent, int):
            errors.append(f"Exponent {self.Exponent} must have type int.")
        if self.AsyncReportThreshold:
            if not isinstance(self.AsyncReportThreshold, float):
                errors.append(f"AsyncReportThreshold {self.AsyncReportThreshold} must have type float.")
        if not isinstance(self.SamplePeriodS, int):
            errors.append(f"SamplePeriodS {self.SamplePeriodS} must have type int.")
        if not isinstance(self.Unit, Unit):
            errors.append(f"Unit {self.Unit} must have type {Unit}.")
        if not isinstance(self.TelemetryName, TelemetryName):
            errors.append(f"TelemetryName {self.TelemetryName} must have type {TelemetryName}.")
        if self.TypeAlias != 'gt.eq.reporting.config.100':
            errors.append(f"Type requires TypeAlias of gt.eq.reporting.config.100, not {self.TypeAlias}.")

        return errors
