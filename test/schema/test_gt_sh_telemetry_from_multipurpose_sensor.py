"""Tests gt.sh.telemetry.from.multipurpose.sensor.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import (
    GtShTelemetryFromMultipurposeSensor_Maker as Maker,
)


def test_gt_sh_telemetry_from_multipurpose_sensor():

    gw_dict = {
        "AboutNodeAliasList": ["a.elt1"],
        "ValueList": [18000],
        "ScadaReadTimeUnixMs": 1656587343297,
        "TelemetryNameList": ["ad19e79c"],
        "TypeAlias": "gt.sh.telemetry.from.multipurpose.sensor.100",
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
        about_node_alias_list=gw_tuple.AboutNodeAliasList,
        value_list=gw_tuple.ValueList,
        scada_read_time_unix_ms=gw_tuple.ScadaReadTimeUnixMs,
        telemetry_name_list=gw_tuple.TelemetryNameList,
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

    orig_value = gw_dict["AboutNodeAliasList"]
    del gw_dict["AboutNodeAliasList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAliasList"] = orig_value

    orig_value = gw_dict["ValueList"]
    del gw_dict["ValueList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = orig_value

    orig_value = gw_dict["ScadaReadTimeUnixMs"]
    del gw_dict["ScadaReadTimeUnixMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ScadaReadTimeUnixMs"] = orig_value

    orig_value = gw_dict["TelemetryNameList"]
    del gw_dict["TelemetryNameList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TelemetryNameList"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["AboutNodeAliasList"]
    gw_dict["AboutNodeAliasList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAliasList"] = [42]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAliasList"] = orig_value

    orig_value = gw_dict["ValueList"]
    gw_dict["ValueList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = [1.1]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = orig_value

    orig_value = gw_dict["ScadaReadTimeUnixMs"]
    gw_dict["ScadaReadTimeUnixMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ScadaReadTimeUnixMs"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            about_node_alias_list=gw_tuple.AboutNodeAliasList,
            value_list=gw_tuple.ValueList,
            scada_read_time_unix_ms=gw_tuple.ScadaReadTimeUnixMs,
            telemetry_name_list="This string is not a list",
        )

    with pytest.raises(MpSchemaError):
        Maker(
            about_node_alias_list=gw_tuple.AboutNodeAliasList,
            value_list=gw_tuple.ValueList,
            scada_read_time_unix_ms=gw_tuple.ScadaReadTimeUnixMs,
            telemetry_name_list=["This is not a TelemetryName Enum."],
        )

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.telemetry.from.multipurpose.sensor.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["AboutNodeAliasList"] = ["a.b-h"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAliasList"] = ["a.elt1"]

    gw_dict["ScadaReadTimeUnixMs"] = 1656245000
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ScadaReadTimeUnixMs"] = 1656587343297

    # End of Test
