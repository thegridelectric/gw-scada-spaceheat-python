"""Tests gt.eq.reporting.config.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config_maker import (
    GtEqReportingConfig_Maker as Maker,
)


def test_gt_eq_reporting_config():

    gw_dict = {
        "ReportOnChange": True,
        "Exponent": 6,
        "ShNodeAlias": "a.elt1",
        "AsyncReportThreshold": 0.2,
        "SamplePeriodS": 300,
        "UnitGtEnumSymbol": "a969ac7c",
        "TelemetryNameGtEnumSymbol": "ad19e79c",
        "TypeAlias": "gt.eq.reporting.config.100",
    }

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple(gw_dict)

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple

    # test Maker init
    t = Maker(
        report_on_change=gw_tuple.ReportOnChange,
        exponent=gw_tuple.Exponent,
        unit=gw_tuple.Unit,
        sh_node_alias=gw_tuple.ShNodeAlias,
        async_report_threshold=gw_tuple.AsyncReportThreshold,
        sample_period_s=gw_tuple.SamplePeriodS,
        telemetry_name=gw_tuple.TelemetryName,
        #
    ).tuple
    assert t == gw_tuple

    ######################################
    # MpSchemaError raised if missing a required attribute
    ######################################

    orig_value = gw_dict["TypeAlias"]
    del gw_dict["TypeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = orig_value

    orig_value = gw_dict["ReportOnChange"]
    del gw_dict["ReportOnChange"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportOnChange"] = orig_value

    orig_value = gw_dict["Exponent"]
    del gw_dict["Exponent"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Exponent"] = orig_value

    orig_value = gw_dict["UnitGtEnumSymbol"]
    del gw_dict["UnitGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["UnitGtEnumSymbol"] = orig_value

    orig_value = gw_dict["ShNodeAlias"]
    del gw_dict["ShNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    orig_value = gw_dict["SamplePeriodS"]
    del gw_dict["SamplePeriodS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SamplePeriodS"] = orig_value

    orig_value = gw_dict["TelemetryNameGtEnumSymbol"]
    del gw_dict["TelemetryNameGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TelemetryNameGtEnumSymbol"] = orig_value

    ######################################
    # Optional attributes can be removed from type
    ######################################

    orig_value = gw_dict["AsyncReportThreshold"]
    del gw_dict["AsyncReportThreshold"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["AsyncReportThreshold"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["ReportOnChange"]
    gw_dict["ReportOnChange"] = "This string is not a boolean."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportOnChange"] = orig_value

    orig_value = gw_dict["Exponent"]
    gw_dict["Exponent"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Exponent"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            report_on_change=gw_tuple.ReportOnChange,
            exponent=gw_tuple.Exponent,
            sh_node_alias=gw_tuple.ShNodeAlias,
            async_report_threshold=gw_tuple.AsyncReportThreshold,
            sample_period_s=gw_tuple.SamplePeriodS,
            telemetry_name=gw_tuple.TelemetryName,
            unit="This is not a Unit Enum.",
        )

    orig_value = gw_dict["ShNodeAlias"]
    gw_dict["ShNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    orig_value = gw_dict["AsyncReportThreshold"]
    gw_dict["AsyncReportThreshold"] = "This string is not a float."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AsyncReportThreshold"] = orig_value

    orig_value = gw_dict["SamplePeriodS"]
    gw_dict["SamplePeriodS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SamplePeriodS"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            report_on_change=gw_tuple.ReportOnChange,
            exponent=gw_tuple.Exponent,
            unit=gw_tuple.Unit,
            sh_node_alias=gw_tuple.ShNodeAlias,
            async_report_threshold=gw_tuple.AsyncReportThreshold,
            sample_period_s=gw_tuple.SamplePeriodS,
            telemetry_name="This is not a TelemetryName Enum.",
        )

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.eq.reporting.config.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ShNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = "a.elt1"

    # End of Test
