"""Tests resistive.heater.component.gt type, version 000"""
import json

import pytest
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema import ResistiveHeaterComponentGt_Maker as Maker


def test_resistive_heater_component_gt_generated() -> None:

    d = {
        "ComponentId": "80f95280-e999-49e0-a0e4-a7faf3b5b3bd",
        "ComponentAttributeClassId": "cf1f2587-7462-4701-b962-d2b264744c1d",
        "DisplayName": "First 4.5 kW boost in tank",
        "HwUid": "aaaa2222",
        "TestedMaxHotMilliOhms": 13714,
        "TestedMaxColdMilliOhms": 14500,
        "TypeName": "resistive.heater.component.gt",
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
        display_name=gtuple.DisplayName,
        hw_uid=gtuple.HwUid,
        tested_max_hot_milli_ohms=gtuple.TestedMaxHotMilliOhms,
        tested_max_cold_milli_ohms=gtuple.TestedMaxColdMilliOhms,
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

    ######################################
    # Optional attributes can be removed from type
    ######################################

    d2 = dict(d)
    if "DisplayName" in d2.keys():
        del d2["DisplayName"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "HwUid" in d2.keys():
        del d2["HwUid"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "TestedMaxHotMilliOhms" in d2.keys():
        del d2["TestedMaxHotMilliOhms"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "TestedMaxColdMilliOhms" in d2.keys():
        del d2["TestedMaxColdMilliOhms"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, TestedMaxHotMilliOhms="13714.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, TestedMaxColdMilliOhms="14500.1")
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

    d2 = dict(d, ComponentId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ComponentAttributeClassId="d4be12d5-33ba-4f1f-b9e5")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    # End of Test
