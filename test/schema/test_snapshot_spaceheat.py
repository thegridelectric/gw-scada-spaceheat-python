"""Tests snapshot.spaceheat.100 type"""
import json

import pytest
from schema.errors import MpSchemaError
from schema.messages import SnapshotSpaceheat_Maker as Maker


def test_snapshot_spaceheat():

    gw_dict = {
        "FromGNodeAlias": "dw1.isone.ct.newhaven.orange1.ta.scada",
        "FromGNodeInstanceId": "0384ef21-648b-4455-b917-58a1172d7fc1",
        "Snapshot": {"TelemetryNameList": ["5a71d4b3"], "AboutNodeAliasList": ["a.elt1.relay"], "ReportTimeUnixMs": 1656363448000, "ValueList": [1], "TypeAlias": "telemetry.snapshot.spaceheat.100"},
        "TypeAlias": "snapshot.spaceheat.100",
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
        from_g_node_instance_id=gw_tuple.FromGNodeInstanceId,
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

    orig_value = gw_dict["FromGNodeAlias"]
    del gw_dict["FromGNodeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

    orig_value = gw_dict["FromGNodeInstanceId"]
    del gw_dict["FromGNodeInstanceId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeInstanceId"] = orig_value

    orig_value = gw_dict["Snapshot"]
    del gw_dict["Snapshot"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Snapshot"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["FromGNodeAlias"]
    gw_dict["FromGNodeAlias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = orig_value

    orig_value = gw_dict["FromGNodeInstanceId"]
    gw_dict["FromGNodeInstanceId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeInstanceId"] = orig_value

    orig_value = gw_dict["Snapshot"]
    gw_dict["Snapshot"] = "Not a TelemetrySnapshotSpaceheat."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Snapshot"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            from_g_node_alias=gw_tuple.FromGNodeAlias,
            from_g_node_instance_id=gw_tuple.FromGNodeInstanceId,
            snapshot="Not a TelemetrySnapshotSpaceheat",
        )

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "snapshot.spaceheat.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["FromGNodeAlias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeAlias"] = "dw1.isone.ct.newhaven.orange1.ta.scada"

    gw_dict["FromGNodeInstanceId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["FromGNodeInstanceId"] = "0384ef21-648b-4455-b917-58a1172d7fc1"

    # End of Test
