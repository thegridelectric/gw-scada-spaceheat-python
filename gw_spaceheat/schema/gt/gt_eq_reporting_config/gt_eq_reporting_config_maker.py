"""Makes gt.eq.reporting.config.100 type"""

import json
from typing import Optional


from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config import GtEqReportingConfig
from schema.errors import MpSchemaError
from schema.enums.unit.unit_map import Unit, UnitMap
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap


class GtEqReportingConfig_Maker():
    type_alias = 'gt.eq.reporting.config.100'

    def __init__(self,
                 report_on_change: bool,
                 exponent: int,
                 sample_period_s: int,
                 unit: Unit,
                 telemetry_name: TelemetryName,
                 async_report_threshold: Optional[float]):

        tuple = GtEqReportingConfig(ReportOnChange=report_on_change,
                                    Exponent=exponent,
                                    Unit=unit,
                                    AsyncReportThreshold=async_report_threshold,
                                    SamplePeriodS=sample_period_s,
                                    TelemetryName=telemetry_name,
                                    )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtEqReportingConfig) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtEqReportingConfig:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtEqReportingConfig:
        if "ReportOnChange" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ReportOnChange")
        if "Exponent" not in d.keys():
            raise MpSchemaError(f"dict {d} missing Exponent")
        if "SamplePeriodS" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SamplePeriodS")
        if "UnitGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing UnitGtEnumSymbol")
        d["Unit"] = UnitMap.gt_to_local(d["UnitGtEnumSymbol"])
        if "TelemetryNameGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TelemetryNameGtEnumSymbol")
        d["TelemetryName"] = TelemetryNameMap.gt_to_local(d["TelemetryNameGtEnumSymbol"])
        if "AsyncReportThreshold" not in d.keys():
            d["AsyncReportThreshold"] = None

        tuple = GtEqReportingConfig(ReportOnChange=d["ReportOnChange"],
                                    Exponent=d["Exponent"],
                                    Unit=d["Unit"],
                                    AsyncReportThreshold=d["AsyncReportThreshold"],
                                    SamplePeriodS=d["SamplePeriodS"],
                                    TelemetryName=d["TelemetryName"],
                                    )
        tuple.check_for_errors()
        return tuple
