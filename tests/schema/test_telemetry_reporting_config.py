"""Tests telemetry.reporting.config type, version 000"""
import json

import pytest
from enums import TelemetryName, Unit
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema import TelemetryReportingConfig_Maker as Maker


def test_telemetry_reporting_config_generated() -> None:

    d = {
        "TelemetryNameGtEnumSymbol": "af39eec9",
        "AboutNodeName": "a.elt1",
        "ReportOnChange": True,
        "SamplePeriodS": 300,
        "Exponent": 6,
        "UnitGtEnumSymbol": "f459a9c3",
        "AsyncReportThreshold": 0.2,
        "NameplateMaxValue": 4000,
        "TypeName": "telemetry.reporting.config",
        "Version": "000",
    }

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple(d)

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gtype = json.dumps(d)
    gtuple = Maker.type_to_tuple(gtype)

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gtuple)) == gtuple

    # test Maker init
    t = Maker(
        telemetry_name=gtuple.TelemetryName,
        about_node_name=gtuple.AboutNodeName,
        report_on_change=gtuple.ReportOnChange,
        sample_period_s=gtuple.SamplePeriodS,
        exponent=gtuple.Exponent,
        unit=gtuple.Unit,
        async_report_threshold=gtuple.AsyncReportThreshold,
        nameplate_max_value=gtuple.NameplateMaxValue,
    ).tuple
    assert t == gtuple

    ######################################
    # MpSchemaError raised if missing a required attribute
    ######################################

    d2 = dict(d)
    del d2["TypeName"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TelemetryNameGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["AboutNodeName"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ReportOnChange"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["SamplePeriodS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Exponent"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["UnitGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "AsyncReportThreshold" in d2.keys():
        del d2["AsyncReportThreshold"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "NameplateMaxValue" in d2.keys():
        del d2["NameplateMaxValue"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, TelemetryNameGtEnumSymbol="hi")
    Maker.dict_to_tuple(d2).TelemetryName = TelemetryName.default()

    d2 = dict(d, ReportOnChange="this is not a boolean")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, SamplePeriodS="300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, Exponent="6.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, UnitGtEnumSymbol="hi")
    Maker.dict_to_tuple(d2).Unit = Unit.default()

    d2 = dict(d, AsyncReportThreshold="this is not a float")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, NameplateMaxValue="4000.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # MpSchemaError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type alias")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    d2 = dict(d, AboutNodeName="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    # End of Test
