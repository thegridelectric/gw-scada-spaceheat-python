"""Tests electric.meter.component.gt type, version 100"""
import json

import pytest
from pydantic import ValidationError

from gwproto.errors import MpSchemaError
from schema.electric_meter_component_gt import ElectricMeterComponentGt_Maker as Maker


def test_electric_meter_component_gt_generated() -> None:


    d = {
        "ComponentId": "245b8267-8a7c-45e0-b9ec-f7cd67cbe716",
        "ComponentAttributeClassId": "739a6e32-bb9c-43bc-a28d-fb61be665522",
        "DisplayName": "Main power meter for Little orange house garage space heat",
        "HwUid": "GC14050323",
        "ModbusHost": "eGauge14875.local",
        "ModbusPort": 502,
        "EgaugeIoList": [
              {
                 "InputConfig":{
                    "Address":9004,
                    "Name":"Garage power",
                    "Description":"change in value",
                    "Type":"f32",
                    "Denominator":1,
                    "Unit":"W",
                    "TypeName":"egauge.register.config",
                    "Version":"000"
                 },
                 "OutputConfig":{
                    "AboutNodeName":"a.elt1",
                    "ReportOnChange":True,
                    "SamplePeriodS":300,
                    "Exponent":1,
                    "AsyncReportThreshold":0.05,
                    "NameplateMaxValue":4500,
                    "TypeName":"telemetry.reporting.config",
                    "Version":"000",
                    "TelemetryNameGtEnumSymbol":"af39eec9",
                    "UnitGtEnumSymbol":"f459a9c3"
                 },
                 "TypeName":"egauge.io",
                 "Version":"000"
              }
           ],
        "TypeName": "electric.meter.component.gt",
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
        component_id=gtuple.ComponentId,
        component_attribute_class_id=gtuple.ComponentAttributeClassId,
        display_name=gtuple.DisplayName,
        hw_uid=gtuple.HwUid,
        modbus_host=gtuple.ModbusHost,
        modbus_port=gtuple.ModbusPort,
        egauge_io_list=gtuple.EgaugeIoList,
        
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
    del d2["EgaugeIoList"]
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

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, ModbusPort="502.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, EgaugeIoList="Not a list.")
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, EgaugeIoList=["Not a list of dicts"])
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, EgaugeIoList= [{"Failed": "Not a GtSimpleSingleStatus"}])
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

    v000_dict = {
            "ComponentId": "8d2be3c8-2ea8-4cb4-8f56-96de9a73ca48",
            "DisplayName": "Apple Freedom EGauge meter",
            "ComponentAttributeClassId": "739a6e32-bb9c-43bc-a28d-fb61be665522",
            "ModbusHost": "eGauge4922.local",
            "ModbusPort": 502,
            "ModbusHwUidRegister": 100,
            "ModbusPowerRegister": 9016,
            "TypeName": "electric.meter.component.gt",
            "Version": "000"
        }

    d2 = Maker.dict_to_tuple(v000_dict)

    # Loses information about the PowerRegister, because the informatio
    # about what ShNode it is for does not exist and so we cannot create
    # an OutputConfig (which is supposed to have that data
    assert d2.EgaugeIoList == []