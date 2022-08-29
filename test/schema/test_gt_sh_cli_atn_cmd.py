"""Tests gt.sh.cli.atn.cmd.110 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd_maker import (
    GtShCliAtnCmd_Maker as Maker,
)


def test_gt_sh_cli_atn_cmd():

    gw_dict = {
        "FromGNodeAlias": "dw1.isone.ct.newhaven.orange1",
        "SendSnapshot": True,
        "FromGNodeId": "e7f7d6cc-08b0-4b36-bbbb-0a1f8447fd32",
        "TypeAlias": "gt.sh.cli.atn.cmd.110",
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
        from_g_node_alias=gw_tuple.FromGNodeAlias,
        send_snapshot=gw_tuple.SendSnapshot,
        from_g_node_id=gw_tuple.FromGNodeId,
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

    orig_value = gw_dict["FromGNodeAlias"]
    del gw_dict["FromGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

    orig_value = gw_dict["SendSnapshot"]
    del gw_dict["SendSnapshot"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendSnapshot"] = orig_value

    orig_value = gw_dict["FromGNodeId"]
    del gw_dict["FromGNodeId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["FromGNodeAlias"]
    gw_dict["FromGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

    orig_value = gw_dict["SendSnapshot"]
    gw_dict["SendSnapshot"] = "This string is not a boolean."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendSnapshot"] = orig_value

    orig_value = gw_dict["FromGNodeId"]
    gw_dict["FromGNodeId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.cli.atn.cmd.110"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["FromGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = "dw1.isone.ct.newhaven.orange1"

    gw_dict["FromGNodeId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = "e7f7d6cc-08b0-4b36-bbbb-0a1f8447fd32"

    # End of Test
