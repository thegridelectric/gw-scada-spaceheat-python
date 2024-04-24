"""Tests gt.powermeter.reporting.config type, version 100"""
import json

import pytest
from pydantic import ValidationError

from gwproto.errors import SchemaError
from gwtypes import GtPowermeterReportingConfig_Maker as Maker


def test_gt_powermeter_reporting_config_generated() -> None:
    d = {
        "ReportingPeriodS": 300,
        "ElectricalQuantityReportingConfigList": [{ "TelemetryNameGtEnumSymbol": "af39eec9", "AboutNodeName": "a.elt1", "ReportOnChange": True, "SamplePeriodS": 300, "Exponent": 6, "UnitGtEnumSymbol": "f459a9c3", "AsyncReportThreshold": 0.2, "NameplateMaxValue": 4000, "TypeName": "telemetry.reporting.config", "Version": "000", }],
        "PollPeriodMs": 1000,
        "HwUid": "1001ab",
        "TypeName": "gt.powermeter.reporting.config",
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
        reporting_period_s=gtuple.ReportingPeriodS,
        electrical_quantity_reporting_config_list=gtuple.ElectricalQuantityReportingConfigList,
        poll_period_ms=gtuple.PollPeriodMs,
        hw_uid=gtuple.HwUid,
        
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
    del d2["ReportingPeriodS"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ElectricalQuantityReportingConfigList"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["PollPeriodMs"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "HwUid" in d2.keys():
        del d2["HwUid"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, ReportingPeriodS="300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, ElectricalQuantityReportingConfigList="Not a list.")
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, ElectricalQuantityReportingConfigList=["Not a list of dicts"])
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, ElectricalQuantityReportingConfigList= [{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, PollPeriodMs="1000.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # SchemaError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
