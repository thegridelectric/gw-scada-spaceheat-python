"""Tests gt.electric.meter.component type, version 000"""
import json

import pytest
from gwproto.errors import MpSchemaError
from pydantic import ValidationError
from schema import GtElectricMeterComponent_Maker as Maker


def test_gt_electric_meter_component_generated() -> None:

    d = {
        "ComponentId": "04ceb282-d7e8-4293-80b5-72455e1a5db3",
        "ComponentAttributeClassId": "c1856e62-d8c0-4352-b79e-6ae05a5294c2",
        "DisplayName": "Main power meter for Little orange house garage space heat",
        "HwUid": "35941_308",
        "ModbusHost": "eGauge4922.local",
        "ModbusPort": 502,
        "ModbusPowerRegister": 9016,
        "ModbusHwUidRegister": 100,
        "TypeName": "gt.electric.meter.component",
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
        modbus_host=gtuple.ModbusHost,
        modbus_port=gtuple.ModbusPort,
        modbus_power_register=gtuple.ModbusPowerRegister,
        modbus_hw_uid_register=gtuple.ModbusHwUidRegister,
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
    if "ModbusHost" in d2.keys():
        del d2["ModbusHost"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "ModbusPort" in d2.keys():
        del d2["ModbusPort"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "ModbusPowerRegister" in d2.keys():
        del d2["ModbusPowerRegister"]
    Maker.dict_to_tuple(d2)

    d2 = dict(d)
    if "ModbusHwUidRegister" in d2.keys():
        del d2["ModbusHwUidRegister"]
    Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, ModbusPort="502.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ModbusPowerRegister="9016.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d, ModbusHwUidRegister="100.1")
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
