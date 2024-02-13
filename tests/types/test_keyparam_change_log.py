"""Tests keyparam.change.log type, version 000"""
import json

import pytest
from pydantic import ValidationError

from gridworks.errors import SchemaError
from gwtypes import KeyparamChangeLog_Maker as Maker
from enums import KindOfParam


def test_keyparam_change_log_generated() -> None:
    d = {
        "AboutNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
        "ChangeTimeUtc": "2022-06-25T12:30:45.678",
        "Author": "Jessica Millar",
        "ParamName": "AdsMaxVoltage",
        "Description": "The maximum voltage used by thermistor temp sensing that rely on the ADS I2C chip. This transitions from being part of the code (pre) to part of the hardware layout (post)",
        "KindGtEnumSymbol": "00000000",
        "Before": 5.1,
        "After": 4.9,
        "TypeName": "keyparam.change.log",
        "Version": "000",
    }

    with pytest.raises(SchemaError):
        Maker.type_to_tuple(d)

    with pytest.raises(SchemaError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gtype = json.dumps(d)
    gtuple = Maker.type_to_tuple(gtype)

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gtuple)) == gtuple

    # test Maker init
    t = Maker(
        about_node_alias=gtuple.AboutNodeAlias,
        change_time_utc=gtuple.ChangeTimeUtc,
        author=gtuple.Author,
        param_name=gtuple.ParamName,
        description=gtuple.Description,
        kind=gtuple.Kind,
    ).tuple
    assert t != gtuple

    d2 = dict(d)
    del d2["Before"]
    del d2["After"]
    gtuple2= Maker.type_to_tuple(json.dumps(d2))
    t2 = Maker(
        about_node_alias=gtuple2.AboutNodeAlias,
        change_time_utc=gtuple2.ChangeTimeUtc,
        author=gtuple2.Author,
        param_name=gtuple2.ParamName,
        description=gtuple2.Description,
        kind=gtuple2.Kind,
    ).tuple
    assert t2 == gtuple2
	

    ######################################
    # SchemaError raised if missing a required attribute
    ######################################

    d2 = dict(d)
    del d2["TypeName"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["AboutNodeAlias"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ChangeTimeUtc"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Author"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["ParamName"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["Description"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2 = dict(d)
    del d2["KindGtEnumSymbol"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    ######################################
    # Behavior on incorrect types
    ######################################

    d2 = dict(d, KindGtEnumSymbol="unknown_symbol")
    Maker.dict_to_tuple(d2).Kind == KindOfParam.default()

    ######################################
    # SchemaError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)

    ######################################
    # SchemaError raised if primitive attributes do not have appropriate property_format
    ######################################

    d2 = dict(d, AboutNodeAlias="a.b-h")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
