"""Tests gt.dispatch.boolean.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_dispatch_boolean.gt_dispatch_boolean_maker import (
    GtDispatchBoolean_Maker as Maker,
)


def test_gt_dispatch_boolean():

    gw_dict = {
        "AboutNodeAlias": "a.elt1.relay",
        "ToGNodeAlias": "dw1.isone.ct.newhaven.orange1.ta.scada",
        "FromGNodeAlias": "dw1.isone.ct.newhaven.orange1",
        "FromGNodeId": "e7f7d6cc-08b0-4b36-bbbb-0a1f8447fd32",
        "RelayState": 0,
        "SendTimeUnixMs": 1657024737661,
        "TypeAlias": "gt.dispatch.boolean.100",
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
        about_node_alias=gw_tuple.AboutNodeAlias,
        to_g_node_alias=gw_tuple.ToGNodeAlias,
        from_g_node_alias=gw_tuple.FromGNodeAlias,
        from_g_node_id=gw_tuple.FromGNodeId,
        relay_state=gw_tuple.RelayState,
        send_time_unix_ms=gw_tuple.SendTimeUnixMs,
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

    orig_value = gw_dict["AboutNodeAlias"]
    del gw_dict["AboutNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAlias"] = orig_value

    orig_value = gw_dict["ToGNodeAlias"]
    del gw_dict["ToGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ToGNodeAlias"] = orig_value

    orig_value = gw_dict["FromGNodeAlias"]
    del gw_dict["FromGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

    orig_value = gw_dict["FromGNodeId"]
    del gw_dict["FromGNodeId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = orig_value

    orig_value = gw_dict["RelayState"]
    del gw_dict["RelayState"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = orig_value

    orig_value = gw_dict["SendTimeUnixMs"]
    del gw_dict["SendTimeUnixMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendTimeUnixMs"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["AboutNodeAlias"]
    gw_dict["AboutNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAlias"] = orig_value

    orig_value = gw_dict["ToGNodeAlias"]
    gw_dict["ToGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ToGNodeAlias"] = orig_value

    orig_value = gw_dict["FromGNodeAlias"]
    gw_dict["FromGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

    orig_value = gw_dict["FromGNodeId"]
    gw_dict["FromGNodeId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = orig_value

    orig_value = gw_dict["RelayState"]
    gw_dict["RelayState"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = orig_value

    orig_value = gw_dict["SendTimeUnixMs"]
    gw_dict["SendTimeUnixMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendTimeUnixMs"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.dispatch.boolean.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["AboutNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["AboutNodeAlias"] = "a.elt1.relay"

    gw_dict["ToGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ToGNodeAlias"] = "dw1.isone.ct.newhaven.orange1.ta.scada"

    gw_dict["FromGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = "dw1.isone.ct.newhaven.orange1"

    gw_dict["FromGNodeId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeId"] = "e7f7d6cc-08b0-4b36-bbbb-0a1f8447fd32"

    gw_dict["RelayState"] = 2
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = 0

    gw_dict["SendTimeUnixMs"] = 1656245000
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendTimeUnixMs"] = 1657024737661

    # End of Test
