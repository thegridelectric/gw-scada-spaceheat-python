"""Tests resistive.heater.cac.gt.100 type"""
import json

import pytest
from gwproto import MpSchemaError
from schema.gt.cacs import ResistiveHeaterCacGt_Maker as Maker


def test_resistive_heater_cac_gt():

    gw_dict = {
        "RatedVoltageV": 240,
        "DisplayName": "Fake Boost Element",
        "NameplateMaxPowerW": 4500,
        "ComponentAttributeClassId": "cf1f2587-7462-4701-b962-d2b264744c1d",
        "MakeModelGtEnumSymbol": "00000000",
        "TypeAlias": "resistive.heater.cac.gt.100",
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
        rated_voltage_v=gw_tuple.RatedVoltageV,
        display_name=gw_tuple.DisplayName,
        nameplate_max_power_w=gw_tuple.NameplateMaxPowerW,
        component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
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

    orig_value = gw_dict["RatedVoltageV"]
    del gw_dict["RatedVoltageV"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RatedVoltageV"] = orig_value

    orig_value = gw_dict["NameplateMaxPowerW"]
    del gw_dict["NameplateMaxPowerW"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["NameplateMaxPowerW"] = orig_value

    orig_value = gw_dict["ComponentAttributeClassId"]
    del gw_dict["ComponentAttributeClassId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = orig_value

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
            rated_voltage_v=gw_tuple.RatedVoltageV,
            display_name=gw_tuple.DisplayName,
            nameplate_max_power_w=gw_tuple.NameplateMaxPowerW,
            component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
            make_model="This is not a MakeModel Enum.",
        )

    orig_value = gw_dict["RatedVoltageV"]
    gw_dict["RatedVoltageV"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["RatedVoltageV"] = orig_value

    orig_value = gw_dict["DisplayName"]
    gw_dict["DisplayName"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["DisplayName"] = orig_value

    orig_value = gw_dict["NameplateMaxPowerW"]
    gw_dict["NameplateMaxPowerW"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["NameplateMaxPowerW"] = orig_value

    orig_value = gw_dict["ComponentAttributeClassId"]
    gw_dict["ComponentAttributeClassId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "resistive.heater.cac.gt.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ComponentAttributeClassId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = "cf1f2587-7462-4701-b962-d2b264744c1d"

    # End of Test
