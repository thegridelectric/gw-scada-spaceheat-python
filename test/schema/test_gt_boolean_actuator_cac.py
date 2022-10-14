"""Tests gt.boolean.actuator.cac.100 type"""
import json

import pytest
from schema.errors import MpSchemaError
from schema.gt.cacs import GtBooleanActuatorCac_Maker as Maker


def test_gt_boolean_actuator_cac():

    gw_dict = {
        "ComponentAttributeClassId": "69f101fc-22e4-4caa-8103-50b8aeb66028",
        "TypicalResponseTimeMs": 400,
        "DisplayName": "Gridworks Simulated Boolean Actuator",
        "MakeModelGtEnumSymbol": "e81d74a8",
        "TypeAlias": "gt.boolean.actuator.cac.100",
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
        make_model=gw_tuple.MakeModel,
        component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
        typical_response_time_ms=gw_tuple.TypicalResponseTimeMs,
        display_name=gw_tuple.DisplayName,
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

    orig_value = gw_dict["MakeModelGtEnumSymbol"]
    del gw_dict["MakeModelGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["MakeModelGtEnumSymbol"] = orig_value

    orig_value = gw_dict["ComponentAttributeClassId"]
    del gw_dict["ComponentAttributeClassId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = orig_value

    orig_value = gw_dict["TypicalResponseTimeMs"]
    del gw_dict["TypicalResponseTimeMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypicalResponseTimeMs"] = orig_value

    ######################################
    # Optional attributes can be removed from type
    ######################################

    orig_value = gw_dict["DisplayName"]
    del gw_dict["DisplayName"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["DisplayName"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    with pytest.raises(MpSchemaError):
        Maker(
            component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
            typical_response_time_ms=gw_tuple.TypicalResponseTimeMs,
            display_name=gw_tuple.DisplayName,
            make_model="This is not a MakeModel Enum.",
        )

    orig_value = gw_dict["ComponentAttributeClassId"]
    gw_dict["ComponentAttributeClassId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = orig_value

    orig_value = gw_dict["TypicalResponseTimeMs"]
    gw_dict["TypicalResponseTimeMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypicalResponseTimeMs"] = orig_value

    orig_value = gw_dict["DisplayName"]
    gw_dict["DisplayName"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["DisplayName"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.boolean.actuator.cac.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ComponentAttributeClassId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = "69f101fc-22e4-4caa-8103-50b8aeb66028"

    # End of Test
