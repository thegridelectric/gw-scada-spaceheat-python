"""Tests gt.dispatch.110 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_dispatch.gt_dispatch_maker import (
    GtDispatch_Maker as Maker,
)


def test_gt_dispatch():

    gw_dict = {
        "ShNodeAlias": "a.elt1.relay",
        "SendTimeUnixMs": 1656869326597,
        "RelayState": 0,
        "TypeAlias": "gt.dispatch.110",
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
        send_time_unix_ms=gw_tuple.SendTimeUnixMs,
        relay_state=gw_tuple.RelayState,
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

    orig_value = gw_dict["SendTimeUnixMs"]
    del gw_dict["SendTimeUnixMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendTimeUnixMs"] = orig_value

    orig_value = gw_dict["RelayState"]
    del gw_dict["RelayState"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["ShNodeAlias"]
    gw_dict["ShNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = orig_value

    orig_value = gw_dict["SendTimeUnixMs"]
    gw_dict["SendTimeUnixMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendTimeUnixMs"] = orig_value

    orig_value = gw_dict["RelayState"]
    gw_dict["RelayState"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.dispatch.110"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ShNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeAlias"] = "a.elt1.relay"

    gw_dict["SendTimeUnixMs"] = 1656245000
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["SendTimeUnixMs"] = 1656869326597

    gw_dict["RelayState"] = 2
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RelayState"] = 0

    # End of Test
