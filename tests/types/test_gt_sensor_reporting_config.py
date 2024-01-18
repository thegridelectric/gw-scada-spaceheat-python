"""Tests gt.sensor.reporting.config type, version 100"""
import json

import pytest
from pydantic import ValidationError

from gridworks.errors import SchemaError
from gwtypes import GtSensorReportingConfig_Maker as Maker
from enums import TelemetryName
from enums import Unit


def test_gt_sensor_reporting_config_generated() -> None:
    d = {
        "TelemetryNameGtEnumSymbol": "af39eec9",
        "ReportingPeriodS": 300,
        "SamplePeriodS": 60,
        "ReportOnChange": True,
        "Exponent": 3,
        "UnitGtEnumSymbol": "f459a9c3",
        "AsyncReportThreshold": 0.05,
        "TypeName": "gt.sensor.reporting.config",
        "Version": "100",
    }

    with pytest.raises(SchemaError):
        Maker.type_to_tuple(d)

    with pytest.raises(SchemaError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gtype = json.dumps(d)
    gtuple = Maker.type_to_tuple(gtype)

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gtuple)) == gtuple

    # test Maker init
    t = Maker(
        telemetry_name=gtuple.TelemetryName,
        reporting_period_s=gtuple.ReportingPeriodS,
        sample_period_s=gtuple.SamplePeriodS,
        report_on_change=gtuple.ReportOnChange,
        exponent=gtuple.Exponent,
        unit=gtuple.Unit,
        async_report_threshold=gtuple.AsyncReportThreshold,
        
    ).tuple
    assert t == gtuple

    ######################################
    # SchemaError raised if missing a required attribute
    ######################################

    d2 = dict(d)
    del d2["TypeName"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TelemetryNameGtEnumSymbol"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ReportingPeriodS"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["SamplePeriodS"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ReportOnChange"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Exponent"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["UnitGtEnumSymbol"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "AsyncReportThreshold" in d2.keys():
        del d2["AsyncReportThreshold"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, TelemetryNameGtEnumSymbol="unknown_symbol")
    Maker.dict_to_tuple(d2).TelemetryName == TelemetryName.default()

    d2 = dict(d, ReportingPeriodS="300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, SamplePeriodS="60.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ReportOnChange="this is not a boolean")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, Exponent="3.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, UnitGtEnumSymbol="unknown_symbol")
    Maker.dict_to_tuple(d2).Unit == Unit.default()

    d2 = dict(d, AsyncReportThreshold="this is not a float")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # SchemaError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
