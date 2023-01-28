"""Tests simple.temp.sensor.cac.gt.000 type"""
import json

import pytest
from gwproto import MpSchemaError
from schema.gt.cacs import SimpleTempSensorCacGt_Maker as Maker


def test_simple_temp_sensor_cac_gt():

    gw_dict = {
        "DisplayName": "Simulated GridWorks high precision water temp sensor",
        "ComponentAttributeClassId": "8a1a1538-ed2d-4829-9c03-f9be1c9f9c83",
        "Exponent": -3,
        "CommsMethod": "SassyMQ",
        "TypicalResponseTimeMs": 880,
        "TelemetryNameGtEnumSymbol": "793505aa",
        "TempUnitGtEnumSymbol": "7d8832f8",
        "MakeModelGtEnumSymbol": "f8b497e8",
        "TypeAlias": "simple.temp.sensor.cac.gt.000",
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
        telemetry_name=gw_tuple.TelemetryName,
        display_name=gw_tuple.DisplayName,
        temp_unit=gw_tuple.TempUnit,
        make_model=gw_tuple.MakeModel,
        component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
        exponent=gw_tuple.Exponent,
        comms_method=gw_tuple.CommsMethod,
        typical_response_time_ms=gw_tuple.TypicalResponseTimeMs,
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

    orig_value = gw_dict["TelemetryNameGtEnumSymbol"]
    del gw_dict["TelemetryNameGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TelemetryNameGtEnumSymbol"] = orig_value

    orig_value = gw_dict["TempUnitGtEnumSymbol"]
    del gw_dict["TempUnitGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TempUnitGtEnumSymbol"] = orig_value

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

    orig_value = gw_dict["Exponent"]
    del gw_dict["Exponent"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Exponent"] = orig_value

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

    orig_value = gw_dict["CommsMethod"]
    del gw_dict["CommsMethod"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["CommsMethod"] = orig_value

    ######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    with pytest.raises(MpSchemaError):
        Maker(
            display_name=gw_tuple.DisplayName,
            temp_unit=gw_tuple.TempUnit,
            make_model=gw_tuple.MakeModel,
            component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
            exponent=gw_tuple.Exponent,
            comms_method=gw_tuple.CommsMethod,
            typical_response_time_ms=gw_tuple.TypicalResponseTimeMs,
            telemetry_name="This is not a TelemetryName Enum.",
        )

    orig_value = gw_dict["DisplayName"]
    gw_dict["DisplayName"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["DisplayName"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            telemetry_name=gw_tuple.TelemetryName,
            display_name=gw_tuple.DisplayName,
            make_model=gw_tuple.MakeModel,
            component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
            exponent=gw_tuple.Exponent,
            comms_method=gw_tuple.CommsMethod,
            typical_response_time_ms=gw_tuple.TypicalResponseTimeMs,
            temp_unit="This is not a Unit Enum.",
        )

    with pytest.raises(MpSchemaError):
        Maker(
            telemetry_name=gw_tuple.TelemetryName,
            display_name=gw_tuple.DisplayName,
            temp_unit=gw_tuple.TempUnit,
            component_attribute_class_id=gw_tuple.ComponentAttributeClassId,
            exponent=gw_tuple.Exponent,
            comms_method=gw_tuple.CommsMethod,
            typical_response_time_ms=gw_tuple.TypicalResponseTimeMs,
            make_model="This is not a MakeModel Enum.",
        )

    orig_value = gw_dict["ComponentAttributeClassId"]
    gw_dict["ComponentAttributeClassId"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = orig_value

    orig_value = gw_dict["Exponent"]
    gw_dict["Exponent"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["Exponent"] = orig_value

    orig_value = gw_dict["CommsMethod"]
    gw_dict["CommsMethod"] = 42
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["CommsMethod"] = orig_value

    orig_value = gw_dict["TypicalResponseTimeMs"]
    gw_dict["TypicalResponseTimeMs"] = 1.1
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypicalResponseTimeMs"] = orig_value

    ######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "simple.temp.sensor.cac.gt.000"

    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    gw_dict["ComponentAttributeClassId"] = "d4be12d5-33ba-4f1f-b9e5"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["ComponentAttributeClassId"] = "8a1a1538-ed2d-4829-9c03-f9be1c9f9c83"

    # End of Test
