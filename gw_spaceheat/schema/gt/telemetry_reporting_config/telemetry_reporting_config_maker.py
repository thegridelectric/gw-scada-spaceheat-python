"""Makes telemetry.reporting.config.000 type"""
import json
from typing import Optional

from schema.gt.telemetry_reporting_config.telemetry_reporting_config import TelemetryReportingConfig
from schema.errors import MpSchemaError
from enums import (
    Unit,
    UnitMap,
)
from enums import (
    TelemetryName,
    TelemetryNameMap,
)


class TelemetryReportingConfig_Maker:
    type_alias = "telemetry.reporting.config.000"

    def __init__(self,
                 report_on_change: bool,
                 exponent: int,
                 unit: Unit,
                 about_node_name: str,
                 sample_period_s: int,
                 telemetry_name: TelemetryName,
                 async_report_threshold: Optional[float],
                 nameplate_max_value: Optional[int]):

        gw_tuple = TelemetryReportingConfig(
            ReportOnChange=report_on_change,
            Exponent=exponent,
            Unit=unit,
            AboutNodeName=about_node_name,
            AsyncReportThreshold=async_report_threshold,
            NameplateMaxValue=nameplate_max_value,
            SamplePeriodS=sample_period_s,
            TelemetryName=telemetry_name,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: TelemetryReportingConfig) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> TelemetryReportingConfig:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> TelemetryReportingConfig:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ReportOnChange" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReportOnChange")
        if "Exponent" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Exponent")
        if "UnitGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing UnitGtEnumSymbol")
        new_d["Unit"] = UnitMap.gt_to_local(new_d["UnitGtEnumSymbol"])
        if "AboutNodeName" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing AboutNodeName")
        if "AsyncReportThreshold" not in new_d.keys():
            new_d["AsyncReportThreshold"] = None
        if "NameplateMaxValue" not in new_d.keys():
            new_d["NameplateMaxValue"] = None
        if "SamplePeriodS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SamplePeriodS")
        if "TelemetryNameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameGtEnumSymbol")
        new_d["TelemetryName"] = TelemetryNameMap.gt_to_local(new_d["TelemetryNameGtEnumSymbol"])

        gw_tuple = TelemetryReportingConfig(
            TypeAlias=new_d["TypeAlias"],
            ReportOnChange=new_d["ReportOnChange"],
            Exponent=new_d["Exponent"],
            Unit=new_d["Unit"],
            AboutNodeName=new_d["AboutNodeName"],
            AsyncReportThreshold=new_d["AsyncReportThreshold"],
            NameplateMaxValue=new_d["NameplateMaxValue"],
            SamplePeriodS=new_d["SamplePeriodS"],
            TelemetryName=new_d["TelemetryName"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
