"""Tests egauge.io type, version 000"""
import json

import pytest
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema import EgaugeIo_Maker as Maker


def test_egauge_io_generated() -> None:

    d = {
        "InputConfig": {
            "Address": 9004,
            "Name": "Garage power",
            "Description": "",
            "Type": "f32",
            "Denominator": 1,
            "Unit": "W",
            "TypeName": "egauge.register.config",
            "Version": "000",
        },
        "OutputConfig": {
            "AboutNodeName": "a.tank1.elts",
            "ReportOnChange": True,
            "SamplePeriodS": 60,
            "Exponent": 0,
            "AsyncReportThreshold": 0.05,
            "NameplateMaxValue": 4500,
            "TypeName": "telemetry.reporting.config",
            "Version": "000",
            "TelemetryNameGtEnumSymbol": "af39eec9",
            "UnitGtEnumSymbol": "f459a9c3",
        },
        "TypeName": "egauge.io",
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
        input_config=gtuple.InputConfig,
        output_config=gtuple.OutputConfig,
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
    del d2["InputConfig"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["OutputConfig"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    ######################################
    # MpSchemaError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type alias")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
