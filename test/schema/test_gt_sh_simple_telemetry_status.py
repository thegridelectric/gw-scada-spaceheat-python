"""Tests gt.sh.simple.telemetry.status.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_simple_telemetry_status.gt_sh_simple_telemetry_status_maker import (
    GtShSimpleTelemetryStatus_Maker as Maker,
)


def test_gt_sh_simple_telemetry_status():

    gw_dict = {
        "ValueList": [0],
        "ReadTimeUnixMsList": [1656443705023],
        "ShNodeAlias": "a.elt1.relay",
        "TelemetryNameGtEnumSymbol": "5a71d4b3",
        "TypeAlias": "gt.sh.simple.telemetry.status.100",
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
        value_list=gw_tuple.ValueList,
        read_time_unix_ms_list=gw_tuple.ReadTimeUnixMsList,
        telemetry_name=gw_tuple.TelemetryName,
        sh_node_alias=gw_tuple.ShNodeAlias,
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

    orig_value = gw_dict["ValueList"]
    del gw_dict["ValueList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = orig_value

    orig_value = gw_dict["ReadTimeUnixMsList"]
    del gw_dict["ReadTimeUnixMsList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReadTimeUnixMsList"] = orig_value

    orig_value = gw_dict["TelemetryNameGtEnumSymbol"]
    del gw_dict["TelemetryNameGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TelemetryNameGtEnumSymbol"] = orig_value

    orig_value = gw_dict["ShNodeAlias"]
    del gw_dict["ShNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["ValueList"]
    gw_dict["ValueList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = [1.1]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = orig_value

    orig_value = gw_dict["ReadTimeUnixMsList"]
    gw_dict["ReadTimeUnixMsList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReadTimeUnixMsList"] = [1.1]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReadTimeUnixMsList"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            value_list=gw_tuple.ValueList,
            read_time_unix_ms_list=gw_tuple.ReadTimeUnixMsList,
            sh_node_alias=gw_tuple.ShNodeAlias,
            telemetry_name="This is not a TelemetryName Enum.",
        )

    orig_value = gw_dict["ShNodeAlias"]
    gw_dict["ShNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.simple.telemetry.status.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ReadTimeUnixMsList"] = [1656245000]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReadTimeUnixMsList"] = [1656443705023]

    gw_dict["ShNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = "a.elt1.relay"

    # End of Test
