"""Tests gt.sh.simple.status.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker import (
    GtShSimpleStatus_Maker as Maker,
)


def test_gt_sh_simple_status():

    gw_dict = {
        "AboutGNodeAlias": "dwjess.isone.nh.orange.1.ta",
        "SlotStartUnixS": 1656443700,
        "ReportingPeriodS": 300,
        "SimpleSingleStatusList": [
            {
                "ReadTimeUnixMsList": [1656443705023],
                "ShNodeAlias": "a.elt1.relay",
                "ValueList": [0],
                "TypeAlias": "gt.sh.simple.single.status.100",
                "TelemetryNameGtEnumSymbol": "5a71d4b3",
            },
            {
                "ReadTimeUnixMsList": [1656443704662, 1656443709089],
                "ShNodeAlias": "a.tank.temp0",
                "ValueList": [66238, 66514],
                "TypeAlias": "gt.sh.simple.single.status.100",
                "TelemetryNameGtEnumSymbol": "793505aa",
            },
        ],
        "TypeAlias": "gt.sh.simple.status.100",
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
        about_g_node_alias=gw_tuple.AboutGNodeAlias,
        slot_start_unix_s=gw_tuple.SlotStartUnixS,
        reporting_period_s=gw_tuple.ReportingPeriodS,
        simple_single_status_list=gw_tuple.SimpleSingleStatusList,
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

    orig_value = gw_dict["AboutGNodeAlias"]
    del gw_dict["AboutGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = orig_value

    orig_value = gw_dict["SlotStartUnixS"]
    del gw_dict["SlotStartUnixS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = orig_value

    orig_value = gw_dict["ReportingPeriodS"]
    del gw_dict["ReportingPeriodS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingPeriodS"] = orig_value

    orig_value = gw_dict["SimpleSingleStatusList"]
    del gw_dict["SimpleSingleStatusList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SimpleSingleStatusList"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["AboutGNodeAlias"]
    gw_dict["AboutGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = orig_value

    orig_value = gw_dict["SlotStartUnixS"]
    gw_dict["SlotStartUnixS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = orig_value

    orig_value = gw_dict["ReportingPeriodS"]
    gw_dict["ReportingPeriodS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingPeriodS"] = orig_value

    orig_value = gw_dict["SimpleSingleStatusList"]
    gw_dict["SimpleSingleStatusList"] = "Not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SimpleSingleStatusList"] = orig_value

    orig_value = gw_dict["SimpleSingleStatusList"]
    gw_dict["SimpleSingleStatusList"] = ["Not even a dict"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)

    gw_dict["SimpleSingleStatusList"] = [{"Failed": "Not a GtSimpleSingleStatus"}]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SimpleSingleStatusList"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            about_g_node_alias=gw_dict["AboutGNodeAlias"],
            slot_start_unix_s=gw_dict["SlotStartUnixS"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            simple_single_status_list=["Not a GtShSimpleSingleStatus100"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            about_g_node_alias=gw_tuple.AboutGNodeAlias,
            slot_start_unix_s=gw_tuple.SlotStartUnixS,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            simple_single_status_list="This string is not a list",
        )

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.simple.status.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["AboutGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = "dwjess.isone.nh.orange.1.ta"

    # End of Test
