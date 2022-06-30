"""Makes gt.sensor.reporting.config.100 type"""

import json
from typing import Optional


from schema.gt.gt_sensor_reporting_config.gt_sensor_reporting_config import GtSensorReportingConfig
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap
from schema.enums.unit.unit_map import Unit, UnitMap


class GtSensorReportingConfig_Maker:
    type_alias = "gt.sensor.reporting.config.100"

    def __init__(
        self,
        report_on_change: bool,
        exponent: int,
        reporting_period_s: int,
        sample_period_s: int,
        telemetry_name: TelemetryName,
        unit: Unit,
        async_report_threshold: Optional[float],
    ):

        tuple = GtSensorReportingConfig(
            ReportOnChange=report_on_change,
            TelemetryName=telemetry_name,
            Unit=unit,
            AsyncReportThreshold=async_report_threshold,
            Exponent=exponent,
            ReportingPeriodS=reporting_period_s,
            SamplePeriodS=sample_period_s,
        )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtSensorReportingConfig) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtSensorReportingConfig:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtSensorReportingConfig:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]

        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ReportOnChange" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReportOnChange")
        if "Exponent" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Exponent")
        if "ReportingPeriodS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReportingPeriodS")
        if "SamplePeriodS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SamplePeriodS")
        if "TelemetryNameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameGtEnumSymbol")
        new_d["TelemetryName"] = TelemetryNameMap.gt_to_local(new_d["TelemetryNameGtEnumSymbol"])
        if "UnitGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing UnitGtEnumSymbol")
        new_d["Unit"] = UnitMap.gt_to_local(new_d["UnitGtEnumSymbol"])
        if "AsyncReportThreshold" not in new_d.keys():
            new_d["AsyncReportThreshold"] = None

        tuple = GtSensorReportingConfig(
            TypeAlias=new_d["TypeAlias"],
            ReportOnChange=new_d["ReportOnChange"],
            TelemetryName=new_d["TelemetryName"],
            Unit=new_d["Unit"],
            AsyncReportThreshold=new_d["AsyncReportThreshold"],
            Exponent=new_d["Exponent"],
            ReportingPeriodS=new_d["ReportingPeriodS"],
            SamplePeriodS=new_d["SamplePeriodS"],
        )
        tuple.check_for_errors()
        return tuple
