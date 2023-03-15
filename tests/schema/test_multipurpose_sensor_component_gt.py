"""Tests multipurpose.sensor.component.gt type, version 000"""
import json

import pytest
from enums import TelemetryName
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema.multipurpose_sensor_component_gt import (
    MultipurposeSensorComponentGt_Maker as Maker,
)


def test_multipurpose_sensor_component_gt_generated() -> None:

    d = {
        "ComponentId": "2ca9e65a-5e85-4eaa-811b-901e940f8d09",
        "ComponentAttributeClassId": "432073b8-4d2b-4e36-9229-73893f33f846",
        "ChannelList": [1],
        "ConfigList": [
            {
                "ReportOnChange": False,
                "Exponent": 3,
                "AboutNodeName": "a.distsourcewater.temp",
                "SamplePeriodS": 60,
                "TypeName": "telemetry.reporting.config",
                "Version": "000",
                "UnitGtEnumSymbol": "ec14bd47",
                "TelemetryNameGtEnumSymbol": "c89d0ba1",
            }
        ],
        "HwUid": "a4f",
        "DisplayName": "TSnap for Almond",
        "TypeName": "multipurpose.sensor.component.gt",
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
        component_id=gtuple.ComponentId,
        component_attribute_class_id=gtuple.ComponentAttributeClassId,
        channel_list=gtuple.ChannelList,
        config_list=gtuple.ConfigList,
        hw_uid=gtuple.HwUid,
        display_name=gtuple.DisplayName,
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
    del d2["ComponentId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ComponentAttributeClassId"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ChannelList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ConfigList"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "HwUid" in d2.keys():
        del d2["HwUid"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "DisplayName" in d2.keys():
        del d2["DisplayName"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, ConfigList="Not a list.")
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ConfigList=["Not a list of dicts"])
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ConfigList=[{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(MpSchemaError):
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

    d2 = dict(d, ComponentId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ComponentAttributeClassId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    # End of Test
