"""Tests gt.powermeter.reporting.config.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_powermeter_reporting_config.gt_powermeter_reporting_config_maker import (
    GtPowermeterReportingConfig_Maker as Maker,
)


def test_gt_powermeter_reporting_config():

    gw_dict = {
        "HwUid": "1001ab",
        "ReportingPeriodS": 300,
        "ElectricalQuantityReportingConfigList": [{"ShNodeAlias": "a.elt1", "ReportOnChange": True, "Exponent": 6, "SamplePeriodS": 5, "AsyncReportThreshold": 0.05, "TypeAlias": "gt.eq.reporting.config.100", "UnitGtEnumSymbol": "a969ac7c", "TelemetryNameGtEnumSymbol": "ad19e79c"}],
        "PollPeriodMs": 1000,
        "TypeAlias": "gt.powermeter.reporting.config.100",
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
        hw_uid=gw_tuple.HwUid,
        reporting_period_s=gw_tuple.ReportingPeriodS,
        electrical_quantity_reporting_config_list=gw_tuple.ElectricalQuantityReportingConfigList,
        poll_period_ms=gw_tuple.PollPeriodMs,
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

    orig_value = gw_dict["ReportingPeriodS"]
    del gw_dict["ReportingPeriodS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingPeriodS"] = orig_value

    orig_value = gw_dict["ElectricalQuantityReportingConfigList"]
    del gw_dict["ElectricalQuantityReportingConfigList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ElectricalQuantityReportingConfigList"] = orig_value

    orig_value = gw_dict["PollPeriodMs"]
    del gw_dict["PollPeriodMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["PollPeriodMs"] = orig_value

    ######################################
    # Optional attributes can be removed from type
    ######################################

    orig_value = gw_dict["HwUid"]
    del gw_dict["HwUid"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["HwUid"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["HwUid"]
    gw_dict["HwUid"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["HwUid"] = orig_value

    orig_value = gw_dict["ReportingPeriodS"]
    gw_dict["ReportingPeriodS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingPeriodS"] = orig_value

    orig_value = gw_dict["ElectricalQuantityReportingConfigList"]
    gw_dict["ElectricalQuantityReportingConfigList"] = "Not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ElectricalQuantityReportingConfigList"] = orig_value

    orig_value = gw_dict["ElectricalQuantityReportingConfigList"]
    gw_dict["ElectricalQuantityReportingConfigList"] = ["Not even a dict"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)

    gw_dict["ElectricalQuantityReportingConfigList"] = [{"Failed": "Not a GtSimpleSingleStatus"}]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ElectricalQuantityReportingConfigList"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            hw_uid=gw_dict["HwUid"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            poll_period_ms=gw_dict["PollPeriodMs"],
            electrical_quantity_reporting_config_list=["Not a GtEqReportingConfig"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            hw_uid=gw_tuple.HwUid,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            poll_period_ms=gw_tuple.PollPeriodMs,
            electrical_quantity_reporting_config_list="This string is not a list",
        )

    orig_value = gw_dict["PollPeriodMs"]
    gw_dict["PollPeriodMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["PollPeriodMs"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.powermeter.reporting.config.100"
