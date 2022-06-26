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
                 sh_node_alias: str,
                 report_on_change: bool,
                 exponent: int,
                 sample_period_s: int,
                 unit: Unit,
                 telemetry_name: TelemetryName,
                 async_report_threshold: Optional[float]):

        tuple = GtEqReportingConfig(ShNodeAlias=sh_node_alias,
                                    ReportOnChange=report_on_change,
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
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]

        if "ShNodeAlias" not in d.keys():
            raise MpSchemaError(f"dict {new_d} missing ShNodeAlias")
        if "ReportOnChange" not in new_d.keys():
            raise MpSchemaError(f"dict {d} missing ReportOnChange")
        if "Exponent" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing Exponent")
        if "SamplePeriodS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing SamplePeriodS")
        if "UnitGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing UnitGtEnumSymbol")
        new_d["Unit"] = UnitMap.gt_to_local(new_d["UnitGtEnumSymbol"])
        if "TelemetryNameGtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TelemetryNameGtEnumSymbol")
        new_d["TelemetryName"] = TelemetryNameMap.gt_to_local(new_d["TelemetryNameGtEnumSymbol"])
        if "AsyncReportThreshold" not in new_d.keys():
            new_d["AsyncReportThreshold"] = None

        tuple = GtEqReportingConfig(ShNodeAlias=new_d["ShNodeAlias"],
                                    ReportOnChange=new_d["ReportOnChange"],
                                    Exponent=new_d["Exponent"],
                                    Unit=new_d["Unit"],
                                    AsyncReportThreshold=new_d["AsyncReportThreshold"],
                                    SamplePeriodS=new_d["SamplePeriodS"],
                                    TelemetryName=new_d["TelemetryName"],
                                    )
        tuple.check_for_errors()
        return tuple
