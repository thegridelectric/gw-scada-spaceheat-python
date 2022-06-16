"""Makes gt.sensor.reporting.config type"""

import json
from typing import Dict, Optional


from schema.gt.gt_sensor_reporting_config.gt_sensor_reporting_config import GtSensorReportingConfig
from schema.errors import MpSchemaError
from schema.enums.telemetry_name.telemetry_name_map import TelemetryName, TelemetryNameMap
from schema.enums.unit.unit_map import Unit, UnitMap


class GtSensorReportingConfig_Maker():
    type_alias = 'gt.sensor.reporting.config.100'

    def __init__(self,
                    report_on_change: bool,
                    exponent: int,
                    scaling_factor: int,
                    reporting_period_s: int,
                    sample_period_s: int,
                    telemetry_name: TelemetryName,
                    unit: Unit,
                    async_report_threshold: Optional[float]):

        tuple = GtSensorReportingConfig(ReportOnChange=report_on_change,
                                            TelemetryName=telemetry_name,
                                            Unit=unit,
                                            AsyncReportThreshold=async_report_threshold,
                                            Exponent=exponent,
                                            ScalingFactor=scaling_factor,
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
            raise MpSchemaError(f'Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) ->  GtSensorReportingConfig:
        if "ReportOnChange" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ReportOnChange")
        if "Exponent" not in d.keys():
            raise MpSchemaError(f"dict {d} missing Exponent")
        if "ScalingFactor" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ScalingFactor")
        if "ReportingPeriodS" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ReportingPeriodS")
        if "SamplePeriodS" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SamplePeriodS")
        if "TelemetryNameGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing TelemetryNameGtEnumSymbol")
        d["TelemetryName"] = TelemetryNameMap.gt_to_local(d["TelemetryNameGtEnumSymbol"])
        if "UnitGtEnumSymbol" not in d.keys():
            raise MpSchemaError(f"dict {d} missing UnitGtEnumSymbol")
        d["Unit"] = UnitMap.gt_to_local(d["UnitGtEnumSymbol"])
        if "AsyncReportThreshold" not in d.keys():
            d["AsyncReportThreshold"] = None

        tuple = GtSensorReportingConfig(ReportOnChange=d["ReportOnChange"],
                                            TelemetryName=d["TelemetryName"],
                                            Unit=d["Unit"],
                                            AsyncReportThreshold=d["AsyncReportThreshold"],
                                            Exponent=d["Exponent"],
                                            ScalingFactor=d["ScalingFactor"],
                                            ReportingPeriodS=d["ReportingPeriodS"],
                                            SamplePeriodS=d["SamplePeriodS"],
                                            )
        tuple.check_for_errors()
        return tuple
