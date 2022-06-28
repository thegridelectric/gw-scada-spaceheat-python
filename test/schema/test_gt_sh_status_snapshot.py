"""Tests gt.sh.status.snapshot.110 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot_maker import (
    GtShStatusSnapshot_Maker as Maker,
)


def test_gt_sh_status_snapshot():

    gw_dict = {
        "TelemetryNameList": ["5a71d4b3", "793505aa"],
        "AboutNodeAliasList": ["a.elt1.relay", "a.tank.temp0"],
        "ReportTimeUnixMs": 1656363448000,
        "ValueList": [1, 66086],
        "TypeAlias": "gt.sh.status.snapshot.110",
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

    ######################################
    # MpSchemaError raised if missing a required attribute
    ######################################

    orig_value = gw_dict["TelemetryNameList"]
    del gw_dict["TelemetryNameList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TelemetryNameList"] = orig_value

    orig_value = gw_dict["AboutNodeAliasList"]
    del gw_dict["AboutNodeAliasList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAliasList"] = orig_value

    orig_value = gw_dict["ReportTimeUnixMs"]
    del gw_dict["ReportTimeUnixMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportTimeUnixMs"] = orig_value

    orig_value = gw_dict["ValueList"]
    del gw_dict["ValueList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["TelemetryNameList"]
    gw_dict["TelemetryNameList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TelemetryNameList"] = ["This string is not a TelemetryNameGtEnumSymbol."]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict) 
    gw_dict["TelemetryNameList"] = orig_value
    
    orig_value = gw_dict["AboutNodeAliasList"]
    gw_dict["AboutNodeAliasList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAliasList"] = [42]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict) 
    gw_dict["AboutNodeAliasList"] = orig_value
    
    orig_value = gw_dict["ReportTimeUnixMs"]
    gw_dict["ReportTimeUnixMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportTimeUnixMs"] = orig_value

    orig_value = gw_dict["ValueList"]
    gw_dict["ValueList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ValueList"] = [1.1]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict) 
    gw_dict["ValueList"] = orig_value
    
    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################
    
    gw_dict["AboutNodeAliasList"] = ["a.b-h"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAliasList"] = ["a.elt1.relay", "a.tank.temp0"]

    gw_dict["ReportTimeUnixMs"] = 1656245000
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportTimeUnixMs"] = 1656363448000