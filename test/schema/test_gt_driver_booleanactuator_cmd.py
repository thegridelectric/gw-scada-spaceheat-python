"""Tests gt.driver.booleanactuator.cmd.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd_maker import (
    GtDriverBooleanactuatorCmd_Maker as Maker,
)


def test_gt_driver_booleanactuator_cmd():

    gw_dict = {
        "RelayState": 0,
        "ShNodeAlias": "a.elt1.relay",
        "CommandTimeUnixMs": 1656869326637,
        "TypeAlias": "gt.driver.booleanactuator.cmd.100",
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
        relay_state=gw_tuple.RelayState,
        sh_node_alias=gw_tuple.ShNodeAlias,
        command_time_unix_ms=gw_tuple.CommandTimeUnixMs,
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

    orig_value = gw_dict["RelayState"]
    del gw_dict["RelayState"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = orig_value

    orig_value = gw_dict["ShNodeAlias"]
    del gw_dict["ShNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    orig_value = gw_dict["CommandTimeUnixMs"]
    del gw_dict["CommandTimeUnixMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommandTimeUnixMs"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["RelayState"]
    gw_dict["RelayState"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = orig_value

    orig_value = gw_dict["ShNodeAlias"]
    gw_dict["ShNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    orig_value = gw_dict["CommandTimeUnixMs"]
    gw_dict["CommandTimeUnixMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommandTimeUnixMs"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.driver.booleanactuator.cmd.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["RelayState"] = 2
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = 0

    gw_dict["ShNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = "a.elt1.relay"

    gw_dict["CommandTimeUnixMs"] = 1656245000
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommandTimeUnixMs"] = 1656869326637

    # End of Test
