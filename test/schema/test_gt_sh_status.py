"""Tests gt.sh.status.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_status.gt_sh_status_maker import (
    GtShStatus_Maker as Maker,
)


def test_gt_sh_status():

    gw_dict = {
        "BooleanactuatorCmdList": [],
        "SimpleTelemetryList": [
            {
                "ReadTimeUnixMsList": [1656443705023],
                "ShNodeAlias": "a.elt1.relay",
                "ValueList": [0],
                "TypeAlias": "gt.sh.simple.telemetry.status.100",
                "TelemetryNameGtEnumSymbol": "5a71d4b3",
            },
            {
                "ReadTimeUnixMsList": [1656443704662, 1656443709089],
                "ShNodeAlias": "a.tank.temp0",
                "ValueList": [66238, 66514],
                "TypeAlias": "gt.sh.simple.telemetry.status.100",
                "TelemetryNameGtEnumSymbol": "793505aa",
            },
        ],
        "MultipurposeTelemetryList": [],
        "SlotStartUnixS": 1656443700,
        "AboutGNodeAlias": "dwjess.isone.nh.orange.1.ta",
        "ReportingPeriodS": 300,
        "TypeAlias": "gt.sh.status.100",
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
        booleanactuator_cmd_list=gw_tuple.BooleanactuatorCmdList,
        simple_telemetry_list=gw_tuple.SimpleTelemetryList,
        multipurpose_telemetry_list=gw_tuple.MultipurposeTelemetryList,
        slot_start_unix_s=gw_tuple.SlotStartUnixS,
        about_g_node_alias=gw_tuple.AboutGNodeAlias,
        reporting_period_s=gw_tuple.ReportingPeriodS,
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

    orig_value = gw_dict["BooleanactuatorCmdList"]
    del gw_dict["BooleanactuatorCmdList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["BooleanactuatorCmdList"] = orig_value

    orig_value = gw_dict["SimpleTelemetryList"]
    del gw_dict["SimpleTelemetryList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SimpleTelemetryList"] = orig_value

    orig_value = gw_dict["MultipurposeTelemetryList"]
    del gw_dict["MultipurposeTelemetryList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["MultipurposeTelemetryList"] = orig_value

    orig_value = gw_dict["SlotStartUnixS"]
    del gw_dict["SlotStartUnixS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = orig_value

    orig_value = gw_dict["AboutGNodeAlias"]
    del gw_dict["AboutGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = orig_value

    orig_value = gw_dict["ReportingPeriodS"]
    del gw_dict["ReportingPeriodS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingPeriodS"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["BooleanactuatorCmdList"]
    gw_dict["BooleanactuatorCmdList"] = "Not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["BooleanactuatorCmdList"] = orig_value

    orig_value = gw_dict["BooleanactuatorCmdList"]
    gw_dict["BooleanactuatorCmdList"] = ["Not even a dict"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)

    gw_dict["BooleanactuatorCmdList"] = [{"Failed": "Not a GtSimpleSingleStatus"}]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["BooleanactuatorCmdList"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            simple_telemetry_list=gw_dict["SimpleTelemetryList"],
            multipurpose_telemetry_list=gw_dict["MultipurposeTelemetryList"],
            slot_start_unix_s=gw_dict["SlotStartUnixS"],
            about_g_node_alias=gw_dict["AboutGNodeAlias"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            booleanactuator_cmd_list=["Not a GtShBooleanactuatorCmdStatus"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            simple_telemetry_list=gw_tuple.SimpleTelemetryList,
            multipurpose_telemetry_list=gw_tuple.MultipurposeTelemetryList,
            slot_start_unix_s=gw_tuple.SlotStartUnixS,
            about_g_node_alias=gw_tuple.AboutGNodeAlias,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            booleanactuator_cmd_list="This string is not a list",
        )

    orig_value = gw_dict["SimpleTelemetryList"]
    gw_dict["SimpleTelemetryList"] = "Not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SimpleTelemetryList"] = orig_value

    orig_value = gw_dict["SimpleTelemetryList"]
    gw_dict["SimpleTelemetryList"] = ["Not even a dict"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)

    gw_dict["SimpleTelemetryList"] = [{"Failed": "Not a GtSimpleSingleStatus"}]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SimpleTelemetryList"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            booleanactuator_cmd_list=gw_dict["BooleanactuatorCmdList"],
            multipurpose_telemetry_list=gw_dict["MultipurposeTelemetryList"],
            slot_start_unix_s=gw_dict["SlotStartUnixS"],
            about_g_node_alias=gw_dict["AboutGNodeAlias"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            simple_telemetry_list=["Not a GtShSimpleTelemetryStatus"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            booleanactuator_cmd_list=gw_tuple.BooleanactuatorCmdList,
            multipurpose_telemetry_list=gw_tuple.MultipurposeTelemetryList,
            slot_start_unix_s=gw_tuple.SlotStartUnixS,
            about_g_node_alias=gw_tuple.AboutGNodeAlias,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            simple_telemetry_list="This string is not a list",
        )

    orig_value = gw_dict["MultipurposeTelemetryList"]
    gw_dict["MultipurposeTelemetryList"] = "Not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["MultipurposeTelemetryList"] = orig_value

    orig_value = gw_dict["MultipurposeTelemetryList"]
    gw_dict["MultipurposeTelemetryList"] = ["Not even a dict"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)

    gw_dict["MultipurposeTelemetryList"] = [{"Failed": "Not a GtSimpleSingleStatus"}]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["MultipurposeTelemetryList"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            booleanactuator_cmd_list=gw_dict["BooleanactuatorCmdList"],
            simple_telemetry_list=gw_dict["SimpleTelemetryList"],
            slot_start_unix_s=gw_dict["SlotStartUnixS"],
            about_g_node_alias=gw_dict["AboutGNodeAlias"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            multipurpose_telemetry_list=["Not a GtShMultipurposeTelemetryStatus"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            booleanactuator_cmd_list=gw_tuple.BooleanactuatorCmdList,
            simple_telemetry_list=gw_tuple.SimpleTelemetryList,
            slot_start_unix_s=gw_tuple.SlotStartUnixS,
            about_g_node_alias=gw_tuple.AboutGNodeAlias,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            multipurpose_telemetry_list="This string is not a list",
        )

    orig_value = gw_dict["SlotStartUnixS"]
    gw_dict["SlotStartUnixS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = orig_value

    orig_value = gw_dict["AboutGNodeAlias"]
    gw_dict["AboutGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = orig_value

    orig_value = gw_dict["ReportingPeriodS"]
    gw_dict["ReportingPeriodS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingPeriodS"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.status.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["SlotStartUnixS"] = 32503683600
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = 1656443700

    gw_dict["AboutGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = "dwjess.isone.nh.orange.1.ta"

    # End of Test
