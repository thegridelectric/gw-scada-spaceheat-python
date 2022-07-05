"""Tests gt.sh.booleanactuator.cmd.status.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status_maker import (
    GtShBooleanactuatorCmdStatus_Maker as Maker,
)


def test_gt_sh_booleanactuator_cmd_status():

    gw_dict = {
        "ShNodeAlias": "a.elt1.relay",
        "RelayStateCommandList": [0],
        "CommandTimeUnixMsList": [1656443704800],
        "TypeAlias": "gt.sh.booleanactuator.cmd.status.100",
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
        sh_node_alias=gw_tuple.ShNodeAlias,
        relay_state_command_list=gw_tuple.RelayStateCommandList,
        command_time_unix_ms_list=gw_tuple.CommandTimeUnixMsList,
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

    orig_value = gw_dict["ShNodeAlias"]
    del gw_dict["ShNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    orig_value = gw_dict["RelayStateCommandList"]
    del gw_dict["RelayStateCommandList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayStateCommandList"] = orig_value

    orig_value = gw_dict["CommandTimeUnixMsList"]
    del gw_dict["CommandTimeUnixMsList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommandTimeUnixMsList"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["ShNodeAlias"]
    gw_dict["ShNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    orig_value = gw_dict["RelayStateCommandList"]
    gw_dict["RelayStateCommandList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayStateCommandList"] = [1.1]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayStateCommandList"] = orig_value

    orig_value = gw_dict["CommandTimeUnixMsList"]
    gw_dict["CommandTimeUnixMsList"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommandTimeUnixMsList"] = [1.1]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommandTimeUnixMsList"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.booleanactuator.cmd.status.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ShNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = "a.elt1.relay"

    gw_dict["RelayStateCommandList"] = [2]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayStateCommandList"] = [0]

    gw_dict["CommandTimeUnixMsList"] = [1656245000]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommandTimeUnixMsList"] = [1656443704800]

    # End of Test
