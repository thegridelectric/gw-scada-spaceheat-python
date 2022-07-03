"""Makes gt.eq.reporting.config.100 type"""
import json
from typing import Optional

from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config import GtEqReportingConfig
from schema.errors import MpSchemaError
from schema.enums.unit.unit_map import (
    Unit,
    UnitMap,
)
from schema.enums.telemetry_name.telemetry_name_map import (
    TelemetryName,
    TelemetryNameMap,
)


class GtEqReportingConfig_Maker:
    type_alias = "gt.eq.reporting.config.100"

    def __init__(self,
                 report_on_change: bool,
                 exponent: int,
                 unit: Unit,
                 sh_node_alias: str,
                 sample_period_s: int,
                 telemetry_name: TelemetryName,
                 async_report_threshold: Optional[float]):

        gw_tuple = GtEqReportingConfig(
            ReportOnChange=report_on_change,
            Exponent=exponent,
            Unit=unit,
            ShNodeAlias=sh_node_alias,
            AsyncReportThreshold=async_report_threshold,
            SamplePeriodS=sample_period_s,
            TelemetryName=telemetry_name,
            #
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtEqReportingConfig) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtEqReportingConfig:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtEqReportingConfig:
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
        if "ShNodeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeAlias")
        if "AsyncReportThreshold" not in new_d.keys():
            new_d["AsyncReportThreshold"] = None
        if "SamplePeriodS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SamplePeriodS")
        if "TelemetryNameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameGtEnumSymbol")
        new_d["TelemetryName"] = TelemetryNameMap.gt_to_local(new_d["TelemetryNameGtEnumSymbol"])

        gw_tuple = GtEqReportingConfig(
            TypeAlias=new_d["TypeAlias"],
            ReportOnChange=new_d["ReportOnChange"],
            Exponent=new_d["Exponent"],
            Unit=new_d["Unit"],
            ShNodeAlias=new_d["ShNodeAlias"],
            AsyncReportThreshold=new_d["AsyncReportThreshold"],
            SamplePeriodS=new_d["SamplePeriodS"],
            TelemetryName=new_d["TelemetryName"],
            #
        )
        gw_tuple.check_for_errors()
        return gw_tuple
