"""Tests gt.sh.cli.scada.response.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response_maker import (
    GtShCliScadaResponse_Maker as Maker,
)


def test_gt_sh_cli_scada_response():

    gw_dict = {
        "Snapshot": {"TelemetryNameList": ["5a71d4b3"], "AboutNodeAliasList": ["a.elt1.relay"], "ReportTimeUnixMs": 1656363448000, "ValueList": [1], "TypeAlias": "gt.sh.status.snapshot.110"},
        "TypeAlias": "gt.sh.cli.scada.response.100",
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
        snapshot=gw_tuple.Snapshot,
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

    orig_value = gw_dict["Snapshot"]
    del gw_dict["Snapshot"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Snapshot"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["Snapshot"]
    gw_dict["Snapshot"] = "Not a GtShStatusSnapshot."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Snapshot"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            snapshot="Not a GtShStatusSnapshot",
        )

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.cli.scada.response.100"
