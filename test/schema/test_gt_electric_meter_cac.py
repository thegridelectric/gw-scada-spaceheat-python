"""Tests gt.electric.meter.cac.100 type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import (
    GtElectricMeterCac_Maker as Maker,
)


def test_gt_electric_meter_cac():

    gw_dict = {
        "ComponentAttributeClassId": "a3d298fb-a4ef-427a-939d-02cc9c9689c1",
        "DisplayName": "Schneider Electric Iem3455 Power Meter",
        "DefaultBaud": 9600,
        "UpdatePeriodMs": 1000,
        "LocalCommInterfaceGtEnumSymbol": "a6a4ac9f",
        "MakeModelGtEnumSymbol": "d300635e",
        "TypeAlias": "gt.electric.meter.cac.100",
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

    ######################################
    # MpSchemaError raised if missing a required attribute
    ######################################

    orig_value = gw_dict["TypeAlias"]
    del gw_dict["TypeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = orig_value

    orig_value = gw_dict["ComponentAttributeClassId"]
    del gw_dict["ComponentAttributeClassId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = orig_value

    orig_value = gw_dict["LocalCommInterfaceGtEnumSymbol"]
    del gw_dict["LocalCommInterfaceGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["LocalCommInterfaceGtEnumSymbol"] = orig_value

    orig_value = gw_dict["MakeModelGtEnumSymbol"]
    del gw_dict["MakeModelGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["MakeModelGtEnumSymbol"] = orig_value

    ######################################
    # Optional attributes can be removed from type
    ######################################

    orig_value = gw_dict["DisplayName"]
    del gw_dict["DisplayName"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["DisplayName"] = orig_value

    orig_value = gw_dict["DefaultBaud"]
    del gw_dict["DefaultBaud"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["DefaultBaud"] = orig_value

    orig_value = gw_dict["UpdatePeriodMs"]
    del gw_dict["UpdatePeriodMs"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["UpdatePeriodMs"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    orig_value = gw_dict["ComponentAttributeClassId"]
    gw_dict["ComponentAttributeClassId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
            make_model=gw_tuple.MakeModel,
            display_name=gw_tuple.DisplayName,
            default_baud=gw_tuple.DefaultBaud,
            update_period_ms=gw_tuple.UpdatePeriodMs,
            local_comm_interface="This is not a LocalCommInterface Enum.",
        )

    with pytest.raises(MpSchemaError):
        Maker(
            component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
            local_comm_interface=gw_tuple.LocalCommInterface,
            display_name=gw_tuple.DisplayName,
            default_baud=gw_tuple.DefaultBaud,
            update_period_ms=gw_tuple.UpdatePeriodMs,
            make_model="This is not a MakeModel Enum.",
        )

    orig_value = gw_dict["DisplayName"]
    gw_dict["DisplayName"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["DisplayName"] = orig_value

    orig_value = gw_dict["DefaultBaud"]
    gw_dict["DefaultBaud"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["DefaultBaud"] = orig_value

    orig_value = gw_dict["UpdatePeriodMs"]
    gw_dict["UpdatePeriodMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["UpdatePeriodMs"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "gt.electric.meter.cac.100"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ComponentAttributeClassId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = "a3d298fb-a4ef-427a-939d-02cc9c9689c1"

    # End of Test
