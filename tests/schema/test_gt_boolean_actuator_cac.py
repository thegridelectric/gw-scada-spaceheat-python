"""Tests gt.boolean.actuator.cac type, version 000"""
import json

import pytest
from enums import MakeModel
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema import GtBooleanActuatorCac_Maker as Maker


def test_gt_boolean_actuator_cac_generated() -> None:

    d = {
        "ComponentAttributeClassId": "69f101fc-22e4-4caa-8103-50b8aeb66028",
        "MakeModelGtEnumSymbol": "9cc57878",
        "DisplayName": "Gridworks Simulated Boolean Actuator",
        "TypicalResponseTimeMs": 400,
        "TypeName": "gt.boolean.actuator.cac",
        "Version": "000",
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
        component_attribute_class_id=gtuple.ComponentAttributeClassId,
        make_model=gtuple.MakeModel,
        display_name=gtuple.DisplayName,
        typical_response_time_ms=gtuple.TypicalResponseTimeMs,
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
    del d2["ComponentAttributeClassId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["MakeModelGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TypicalResponseTimeMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "DisplayName" in d2.keys():
        del d2["DisplayName"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, MakeModelGtEnumSymbol="hi")
    Maker.dict_to_tuple(d2).MakeModel = MakeModel.default()

    d2 = dict(d, TypicalResponseTimeMs="400.1")
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

    d2 = dict(d, ComponentAttributeClassId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    # End of Test
