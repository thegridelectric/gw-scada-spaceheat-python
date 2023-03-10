"""Tests multipurpose.sensor.cac.gt type, version 000"""
import json

import pytest
from enums import MakeModel, TelemetryName, Unit
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema import MultipurposeSensorCacGt_Maker as Maker


def test_multipurpose_sensor_cac_gt_generated() -> None:

    d = {
        "ComponentAttributeClassId": "8a1a1538-ed2d-4829-9c03-f9be1c9f9c83",
        "MakeModelGtEnumSymbol": "09185ae3",
        "PollPeriodMs": 880,
        "Exponent": -3,
        "TempUnitGtEnumSymbol": "8e6dd6dd",
        "MaxThermistors": 12,
        "TelemetryNameList": ["22641963"],
        "DisplayName": "Simulated GridWorks high precision water temp sensor",
        "CommsMethod": "I2C",
        "TypeName": "multipurpose.sensor.cac.gt",
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
        poll_period_ms=gtuple.PollPeriodMs,
        exponent=gtuple.Exponent,
        temp_unit=gtuple.TempUnit,
        telemetry_name_list=gtuple.TelemetryNameList,
        max_thermistors=gtuple.MaxThermistors,
        display_name=gtuple.DisplayName,
        comms_method=gtuple.CommsMethod,
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
    del d2["PollPeriodMs"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Exponent"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TempUnitGtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["TelemetryNameList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "MaxThermistors" in d2.keys():
        del d2["MaxThermistors"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "DisplayName" in d2.keys():
        del d2["DisplayName"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "CommsMethod" in d2.keys():
        del d2["CommsMethod"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, MakeModelGtEnumSymbol="hi")
    Maker.dict_to_tuple(d2).MakeModel = MakeModel.default()

    d2 = dict(d, PollPeriodMs="880.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, Exponent="-3.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, TempUnitGtEnumSymbol="hi")
    Maker.dict_to_tuple(d2).TempUnit = Unit.default()

    d2 = dict(d, MaxThermistors="12.1")
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
