"""Tests gt.sh.node.120 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_sh_node.gt_sh_node_maker import (
    GtShNode_Maker as Maker,
)


def test_gt_sh_node():

    gw_dict = {
        "DisplayName": "Temp Sensor on distribution pipe out of tank",
        "ReportingSamplePeriodS": 60,
        "ShNodeId": "66a4a5e7-f160-424a-8ad5-f6554bf9a99a",
        "Alias": "a.tank.out.temp1",
        "ActorClassGtEnumSymbol": "dae4b2f0",
        "RoleGtEnumSymbol": "c480f612",
        "ComponentId": "a16d7bb6-2606-4ad1-b6b4-be80b5d84a6e",
        "TypeAlias": "gt.sh.node.120",
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
        component_id=gw_tuple.ComponentId,
        display_name=gw_tuple.DisplayName,
        actor_class=gw_tuple.ActorClass,
        role=gw_tuple.Role,
        reporting_sample_period_s=gw_tuple.ReportingSamplePeriodS,
        sh_node_id=gw_tuple.ShNodeId,
        alias=gw_tuple.Alias,
    ).tuple
    assert t == gw_tuple

    ######################################
    # Dataclass related tests
    ######################################

    dc = Maker.tuple_to_dc(gw_tuple)
    assert gw_tuple == Maker.dc_to_tuple(dc)
    assert Maker.type_to_dc(Maker.dc_to_type(dc)) == dc

    ######################################
    # MpSchemaError raised if missing a required attribute
    ######################################

    orig_value = gw_dict["TypeAlias"]
    del gw_dict["TypeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = orig_value

    orig_value = gw_dict["ActorClassGtEnumSymbol"]
    del gw_dict["ActorClassGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ActorClassGtEnumSymbol"] = orig_value

    orig_value = gw_dict["RoleGtEnumSymbol"]
    del gw_dict["RoleGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RoleGtEnumSymbol"] = orig_value

    orig_value = gw_dict["ShNodeId"]
    del gw_dict["ShNodeId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeId"] = orig_value

    orig_value = gw_dict["Alias"]
    del gw_dict["Alias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Alias"] = orig_value

    ######################################
    # Optional attributes can be removed from type
    ######################################

    orig_value = gw_dict["ComponentId"]
    del gw_dict["ComponentId"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["ComponentId"] = orig_value

    orig_value = gw_dict["DisplayName"]
    del gw_dict["DisplayName"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["DisplayName"] = orig_value

    orig_value = gw_dict["ReportingSamplePeriodS"]
    del gw_dict["ReportingSamplePeriodS"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["ReportingSamplePeriodS"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["ComponentId"]
    gw_dict["ComponentId"] = "Not a dataclass id"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentId"] = orig_value

    orig_value = gw_dict["DisplayName"]
    gw_dict["DisplayName"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["DisplayName"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            component_id=gw_tuple.ComponentId,
            display_name=gw_tuple.DisplayName,
            role=gw_tuple.Role,
            reporting_sample_period_s=gw_tuple.ReportingSamplePeriodS,
            sh_node_id=gw_tuple.ShNodeId,
            alias=gw_tuple.Alias,
            actor_class="This is not a ActorClass Enum.",
        )

    with pytest.raises(MpSchemaError):
        Maker(
            component_id=gw_tuple.ComponentId,
            display_name=gw_tuple.DisplayName,
            actor_class=gw_tuple.ActorClass,
            reporting_sample_period_s=gw_tuple.ReportingSamplePeriodS,
            sh_node_id=gw_tuple.ShNodeId,
            alias=gw_tuple.Alias,
            role="This is not a Role Enum.",
        )

    orig_value = gw_dict["ReportingSamplePeriodS"]
    gw_dict["ReportingSamplePeriodS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingSamplePeriodS"] = orig_value

    orig_value = gw_dict["ShNodeId"]
    gw_dict["ShNodeId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeId"] = orig_value

    orig_value = gw_dict["Alias"]
    gw_dict["Alias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Alias"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.sh.node.120"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ShNodeId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeId"] = "66a4a5e7-f160-424a-8ad5-f6554bf9a99a"

    gw_dict["Alias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Alias"] = "a.tank.out.temp1"

    # End of Test
