"""Tests spaceheat.node.gt.100 type"""
import json

import pytest
from enums import Role
from enums import RoleMap
from gwproto import MpSchemaError
from schema.gt.spaceheat_node_gt.spaceheat_node_gt_maker import (
    SpaceheatNodeGt_Maker as Maker,
)


def test_spaceheat_node_gt():

    gw_dict_1 = {
        "Alias": "a.tank.temp0",
        "RoleGtEnumSymbol": "73308a1f",
        "ActorClassGtEnumSymbol": "dae4b2f0",
        "DisplayName": "Tank temp sensor temp0 (on top)",
        "ShNodeId": "3593a10a-4335-447a-b62e-e123788a134a",
        "ComponentId": "f516467e-7691-42c8-8525-f7d49bb135ce",
        "ReportingSamplePeriodS": 5,
        "TypeAlias": "spaceheat.node.gt.100",
    }

    gw_type_1 = json.dumps(gw_dict_1)
    gw_tuple_1 = Maker.type_to_tuple(gw_type_1)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple_1)) == gw_tuple_1

    gw_dict = {
        "Alias": "a.elt1",
        "RatedVoltageV": 240,
        "ShNodeId": "41f2ae73-8782-406d-bda7-a95b5abe317e",
        "DisplayName": "First boost element",
        "TypicalVoltageV": 225,
        "RoleGtEnumSymbol": "99c5f326",
        "ActorClassGtEnumSymbol": "00000000",
        "ComponentId": "80f95280-e999-49e0-a0e4-a7faf3b5b3bd",
        "TypeAlias": "spaceheat.node.gt.100",
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
        alias=gw_tuple.Alias,
        reporting_sample_period_s=gw_tuple.ReportingSamplePeriodS,
        role=gw_tuple.Role,
        component_id=gw_tuple.ComponentId,
        rated_voltage_v=gw_tuple.RatedVoltageV,
        actor_class=gw_tuple.ActorClass,
        sh_node_id=gw_tuple.ShNodeId,
        display_name=gw_tuple.DisplayName,
        typical_voltage_v=gw_tuple.TypicalVoltageV,
        #
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

    orig_value = gw_dict["Alias"]
    del gw_dict["Alias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Alias"] = orig_value

    orig_value = gw_dict["RoleGtEnumSymbol"]
    del gw_dict["RoleGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RoleGtEnumSymbol"] = orig_value

    orig_value = gw_dict["ActorClassGtEnumSymbol"]
    del gw_dict["ActorClassGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ActorClassGtEnumSymbol"] = orig_value

    orig_value = gw_dict["ShNodeId"]
    del gw_dict["ShNodeId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeId"] = orig_value

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

    orig_value = gw_dict["TypicalVoltageV"]
    del gw_dict["TypicalVoltageV"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["TypicalVoltageV"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["Alias"]
    gw_dict["Alias"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Alias"] = orig_value

    gw_dict["ReportingSamplePeriodS"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ReportingSamplePeriodS"] = None

    with pytest.raises(MpSchemaError):
        Maker(
            alias=gw_tuple.Alias,
            reporting_sample_period_s=gw_tuple.ReportingSamplePeriodS,
            component_id=gw_tuple.ComponentId,
            rated_voltage_v=gw_tuple.RatedVoltageV,
            actor_class=gw_tuple.ActorClass,
            sh_node_id=gw_tuple.ShNodeId,
            display_name=gw_tuple.DisplayName,
            typical_voltage_v=gw_tuple.TypicalVoltageV,
            role="This is not a Role Enum.",
        )

    orig_value = gw_dict["ComponentId"]
    gw_dict["ComponentId"] = "Not a dataclass id"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentId"] = orig_value

    orig_value = gw_dict["RatedVoltageV"]
    gw_dict["RatedVoltageV"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RatedVoltageV"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            alias=gw_tuple.Alias,
            reporting_sample_period_s=gw_tuple.ReportingSamplePeriodS,
            role=gw_tuple.Role,
            component_id=gw_tuple.ComponentId,
            rated_voltage_v=gw_tuple.RatedVoltageV,
            sh_node_id=gw_tuple.ShNodeId,
            display_name=gw_tuple.DisplayName,
            typical_voltage_v=gw_tuple.TypicalVoltageV,
            actor_class="This is not a ActorClass Enum.",
        )

    orig_value = gw_dict["ShNodeId"]
    gw_dict["ShNodeId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeId"] = orig_value

    orig_value = gw_dict["DisplayName"]
    gw_dict["DisplayName"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["DisplayName"] = orig_value

    orig_value = gw_dict["TypicalVoltageV"]
    gw_dict["TypicalVoltageV"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypicalVoltageV"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "spaceheat.node.gt.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["Alias"] = "a.b-h"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Alias"] = "a.elt1"

    gw_dict["ShNodeId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ShNodeId"] = "41f2ae73-8782-406d-bda7-a95b5abe317e"

    # End of Derived Test

    #######################################
    # Test check_rated_voltage_existence
    ######################################

    gw_dict["RoleGtEnumSymbol"] = RoleMap.local_to_gt_dict[Role.BoostElement]
    orig_value = gw_dict["RatedVoltageV"]
    del gw_dict["RatedVoltageV"]
    gw_type = json.dumps(gw_dict)
    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple(gw_type)

    other_roles = set(RoleMap.local_to_gt_dict.keys()) - set([Role.BoostElement])
    for role in other_roles:
        gw_dict["RoleGtEnumSymbol"] = RoleMap.local_to_gt_dict[role]
        assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple

    gw_dict["RatedVoltageV"] = orig_value
