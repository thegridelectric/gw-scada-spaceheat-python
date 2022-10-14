"""Tests gt.sh.status.110 type"""
import json

import pytest
from schema.errors import MpSchemaError
from schema.messages import GtShStatus_Maker as Maker


def test_gt_sh_status():

    gw_dict = {
        "SlotStartUnixS": 1656945300,
        "SimpleTelemetryList": [
            {
                "ValueList": [0, 1],
                "ReadTimeUnixMsList": [1656945400527, 1656945414270],
                "ShNodeAlias": "a.elt1.relay",
                "TypeAlias": "gt.sh.simple.telemetry.status.100",
                "TelemetryNameGtEnumSymbol": "5a71d4b3",
            }
        ],
        "AboutGNodeAlias": "dw1.isone.ct.newhaven.orange1.ta",
        "BooleanactuatorCmdList": [
            {
                "ShNodeAlias": "a.elt1.relay",
                "RelayStateCommandList": [1],
                "CommandTimeUnixMsList": [1656945413464],
                "TypeAlias": "gt.sh.booleanactuator.cmd.status.100",
            }
        ],
        "FromGNodeAlias": "dw1.isone.ct.newhaven.orange1.ta.scada",
        "MultipurposeTelemetryList": [
            {
                "AboutNodeAlias": "a.elt1",
                "ValueList": [18000],
                "ReadTimeUnixMsList": [1656945390152],
                "SensorNodeAlias": "a.m",
                "TypeAlias": "gt.sh.multipurpose.telemetry.status.100",
                "TelemetryNameGtEnumSymbol": "ad19e79c",
            }
        ],
        "FromGNodeId": "0384ef21-648b-4455-b917-58a1172d7fc1",
        "StatusUid": "dedc25c2-8276-4b25-abd6-f53edc79b62b",
        "ReportingPeriodS": 300,
        "TypeAlias": "gt.sh.status.110",
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
        slot_start_unix_s=gw_tuple.SlotStartUnixS,
        simple_telemetry_list=gw_tuple.SimpleTelemetryList,
        about_g_node_alias=gw_tuple.AboutGNodeAlias,
        booleanactuator_cmd_list=gw_tuple.BooleanactuatorCmdList,
        from_g_node_alias=gw_tuple.FromGNodeAlias,
        multipurpose_telemetry_list=gw_tuple.MultipurposeTelemetryList,
        from_g_node_id=gw_tuple.FromGNodeId,
        status_uid=gw_tuple.StatusUid,
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

    orig_value = gw_dict["SlotStartUnixS"]
    del gw_dict["SlotStartUnixS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = orig_value

    orig_value = gw_dict["SimpleTelemetryList"]
    del gw_dict["SimpleTelemetryList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SimpleTelemetryList"] = orig_value

    orig_value = gw_dict["AboutGNodeAlias"]
    del gw_dict["AboutGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = orig_value

    orig_value = gw_dict["BooleanactuatorCmdList"]
    del gw_dict["BooleanactuatorCmdList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["BooleanactuatorCmdList"] = orig_value

    orig_value = gw_dict["FromGNodeAlias"]
    del gw_dict["FromGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

    orig_value = gw_dict["MultipurposeTelemetryList"]
    del gw_dict["MultipurposeTelemetryList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["MultipurposeTelemetryList"] = orig_value

    orig_value = gw_dict["FromGNodeId"]
    del gw_dict["FromGNodeId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = orig_value

    orig_value = gw_dict["StatusUid"]
    del gw_dict["StatusUid"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["StatusUid"] = orig_value

    orig_value = gw_dict["ReportingPeriodS"]
    del gw_dict["ReportingPeriodS"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingPeriodS"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["SlotStartUnixS"]
    gw_dict["SlotStartUnixS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = orig_value

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
            slot_start_unix_s=gw_dict["SlotStartUnixS"],
            about_g_node_alias=gw_dict["AboutGNodeAlias"],
            booleanactuator_cmd_list=gw_dict["BooleanactuatorCmdList"],
            from_g_node_alias=gw_dict["FromGNodeAlias"],
            multipurpose_telemetry_list=gw_dict["MultipurposeTelemetryList"],
            from_g_node_id=gw_dict["FromGNodeId"],
            status_uid=gw_dict["StatusUid"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            simple_telemetry_list=["Not a GtShSimpleTelemetryStatus"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            slot_start_unix_s=gw_tuple.SlotStartUnixS,
            about_g_node_alias=gw_tuple.AboutGNodeAlias,
            booleanactuator_cmd_list=gw_tuple.BooleanactuatorCmdList,
            from_g_node_alias=gw_tuple.FromGNodeAlias,
            multipurpose_telemetry_list=gw_tuple.MultipurposeTelemetryList,
            from_g_node_id=gw_tuple.FromGNodeId,
            status_uid=gw_tuple.StatusUid,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            simple_telemetry_list="This string is not a list",
        )

    orig_value = gw_dict["AboutGNodeAlias"]
    gw_dict["AboutGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = orig_value

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
            slot_start_unix_s=gw_dict["SlotStartUnixS"],
            simple_telemetry_list=gw_dict["SimpleTelemetryList"],
            about_g_node_alias=gw_dict["AboutGNodeAlias"],
            from_g_node_alias=gw_dict["FromGNodeAlias"],
            multipurpose_telemetry_list=gw_dict["MultipurposeTelemetryList"],
            from_g_node_id=gw_dict["FromGNodeId"],
            status_uid=gw_dict["StatusUid"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            booleanactuator_cmd_list=["Not a GtShBooleanactuatorCmdStatus"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            slot_start_unix_s=gw_tuple.SlotStartUnixS,
            simple_telemetry_list=gw_tuple.SimpleTelemetryList,
            about_g_node_alias=gw_tuple.AboutGNodeAlias,
            from_g_node_alias=gw_tuple.FromGNodeAlias,
            multipurpose_telemetry_list=gw_tuple.MultipurposeTelemetryList,
            from_g_node_id=gw_tuple.FromGNodeId,
            status_uid=gw_tuple.StatusUid,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            booleanactuator_cmd_list="This string is not a list",
        )

    orig_value = gw_dict["FromGNodeAlias"]
    gw_dict["FromGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

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
            slot_start_unix_s=gw_dict["SlotStartUnixS"],
            simple_telemetry_list=gw_dict["SimpleTelemetryList"],
            about_g_node_alias=gw_dict["AboutGNodeAlias"],
            booleanactuator_cmd_list=gw_dict["BooleanactuatorCmdList"],
            from_g_node_alias=gw_dict["FromGNodeAlias"],
            from_g_node_id=gw_dict["FromGNodeId"],
            status_uid=gw_dict["StatusUid"],
            reporting_period_s=gw_dict["ReportingPeriodS"],
            multipurpose_telemetry_list=["Not a GtShMultipurposeTelemetryStatus"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            slot_start_unix_s=gw_tuple.SlotStartUnixS,
            simple_telemetry_list=gw_tuple.SimpleTelemetryList,
            about_g_node_alias=gw_tuple.AboutGNodeAlias,
            booleanactuator_cmd_list=gw_tuple.BooleanactuatorCmdList,
            from_g_node_alias=gw_tuple.FromGNodeAlias,
            from_g_node_id=gw_tuple.FromGNodeId,
            status_uid=gw_tuple.StatusUid,
            reporting_period_s=gw_tuple.ReportingPeriodS,
            multipurpose_telemetry_list="This string is not a list",
        )

    orig_value = gw_dict["FromGNodeId"]
    gw_dict["FromGNodeId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = orig_value

    orig_value = gw_dict["StatusUid"]
    gw_dict["StatusUid"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["StatusUid"] = orig_value

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
    gw_dict["TypeAlias"] = "gt.sh.status.110"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["SlotStartUnixS"] = 32503683600
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SlotStartUnixS"] = 1656945300

    gw_dict["AboutGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutGNodeAlias"] = "dw1.isone.ct.newhaven.orange1.ta"

    gw_dict["FromGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = "dw1.isone.ct.newhaven.orange1.ta.scada"

    gw_dict["FromGNodeId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = "0384ef21-648b-4455-b917-58a1172d7fc1"

    gw_dict["StatusUid"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["StatusUid"] = "dedc25c2-8276-4b25-abd6-f53edc79b62b"

    # End of Test
