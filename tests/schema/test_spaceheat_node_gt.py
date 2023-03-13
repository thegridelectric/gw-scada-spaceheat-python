"""Tests spaceheat.node.gt type, version 100"""
import json

import pytest
from enums import ActorClass, Role
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema import SpaceheatNodeGt_Maker as Maker


def test_spaceheat_node_gt_generated() -> None:

    d = {
        "ShNodeId": "41f2ae73-8782-406d-bda7-a95b5abe317e",
        "Alias": "a.elt1",
        "ActorClassGtEnumSymbol": "638bf97b",
        "RoleGtEnumSymbol": "5a28eb2e",
        "DisplayName": "First boost element",
        "ComponentId": "80f95280-e999-49e0-a0e4-a7faf3b5b3bd",
        "ReportingSamplePeriodS": 300,
        "RatedVoltageV": 240,
        "TypicalVoltageV": 225,
        "InPowerMetering": False,
        "TypeName": "spaceheat.node.gt",
        "Version": "100",
    }

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple(d)

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gtype = json.dumps(d)
    gtuple = Maker.type_to_tuple(gtype)

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gtuple)) == gtuple

    # test Maker init
    t = Maker(
        sh_node_id=gtuple.ShNodeId,
        alias=gtuple.Alias,
        actor_class=gtuple.ActorClass,
        role=gtuple.Role,
        display_name=gtuple.DisplayName,
        component_id=gtuple.ComponentId,
        reporting_sample_period_s=gtuple.ReportingSamplePeriodS,
        rated_voltage_v=gtuple.RatedVoltageV,
        typical_voltage_v=gtuple.TypicalVoltageV,
        in_power_metering=gtuple.InPowerMetering,
    ).tuple
    assert t == gtuple

    ######################################
    # Dataclass related tests
    ######################################

    dc = Maker.tuple_to_dc(gtuple)
    assert gtuple == Maker.dc_to_tuple(dc)
    assert Maker.type_to_dc(Maker.dc_to_type(dc)) == dc

    ######################################
    # MpSchemaError raised if missing a required attribute
    ######################################

    d2 = dict(d)
    del d2["TypeName"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ShNodeId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Alias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ActorClassGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["RoleGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "DisplayName" in d2.keys():
        del d2["DisplayName"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "ComponentId" in d2.keys():
        del d2["ComponentId"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "ReportingSamplePeriodS" in d2.keys():
        del d2["ReportingSamplePeriodS"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "RatedVoltageV" in d2.keys():
        del d2["RatedVoltageV"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "TypicalVoltageV" in d2.keys():
        del d2["TypicalVoltageV"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "InPowerMetering" in d2.keys():
        del d2["InPowerMetering"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, ActorClassGtEnumSymbol="hi")
    Maker.dict_to_tuple(d2).ActorClass = ActorClass.default()

    d2 = dict(d, RoleGtEnumSymbol="hi")
    Maker.dict_to_tuple(d2).Role = Role.default()

    d2 = dict(d, ReportingSamplePeriodS="300.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, RatedVoltageV="240.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, TypicalVoltageV="225.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, InPowerMetering="this is not a boolean")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # MpSchemaError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type alias")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    d2 = dict(d, ShNodeId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, Alias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    # End of Test
