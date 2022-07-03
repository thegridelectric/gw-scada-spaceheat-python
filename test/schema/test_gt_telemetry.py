"""Tests gt.telemetry.110 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_telemetry.gt_telemetry_maker import (
    GtTelemetry_Maker as Maker,
)


def test_gt_telemetry():

    gw_dict = {
        "ScadaReadTimeUnixMs": 1656513094288,
        "Value": 63430,
        "Exponent": 3,
        "NameGtEnumSymbol": "793505aa",
        "TypeAlias": "gt.telemetry.110",
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
        scada_read_time_unix_ms=gw_tuple.ScadaReadTimeUnixMs,
        value=gw_tuple.Value,
        name=gw_tuple.Name,
        exponent=gw_tuple.Exponent,
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

    orig_value = gw_dict["ScadaReadTimeUnixMs"]
    del gw_dict["ScadaReadTimeUnixMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ScadaReadTimeUnixMs"] = orig_value

    orig_value = gw_dict["Value"]
    del gw_dict["Value"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Value"] = orig_value

    orig_value = gw_dict["NameGtEnumSymbol"]
    del gw_dict["NameGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["NameGtEnumSymbol"] = orig_value

    orig_value = gw_dict["Exponent"]
    del gw_dict["Exponent"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Exponent"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["ScadaReadTimeUnixMs"]
    gw_dict["ScadaReadTimeUnixMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ScadaReadTimeUnixMs"] = orig_value

    orig_value = gw_dict["Value"]
    gw_dict["Value"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Value"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            scada_read_time_unix_ms=gw_tuple.ScadaReadTimeUnixMs,
            value=gw_tuple.Value,
            exponent=gw_tuple.Exponent,
            name="This is not a TelemetryName Enum.",
        )

    orig_value = gw_dict["Exponent"]
    gw_dict["Exponent"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Exponent"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.telemetry.110"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ScadaReadTimeUnixMs"] = 1656245000
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ScadaReadTimeUnixMs"] = 1656513094288

    # End of Test
