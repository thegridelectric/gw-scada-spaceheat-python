"""Type gt.boolean.actuator.cac, version 000"""
import json
from enum import auto
from typing import Any, Dict, List, Literal, Optional

from data_classes.cacs.boolean_actuator_cac import BooleanActuatorCac
from enums import MakeModel as EnumMakeModel
from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError
from gwproto.message import as_enum
from pydantic import BaseModel, Field, validator


class SpaceheatMakeModel000SchemaEnum:
    enum_name: str = "spaceheat.make.model.000"
    symbols: List[str] = [
        "00000000",
        "beb6d3fb",
        "fabfa505",
        "acd93fb3",
        "d0178dc3",
        "f8b497e8",
        "076da322",
        "d300635e",
        "e81d74a8",
        "c75d269f",
        "3042c432",
        "d0b0e375",
        "a8d9a70d",
        "08da3f7d",
    ]

    @classmethod
    def is_symbol(cls, candidate: str) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class SpaceheatMakeModel000(StrEnum):
    UNKNOWNMAKE__UNKNOWNMODEL = auto()
    EGAUGE__4030 = auto()
    NCD__PR814SPST = auto()
    ADAFRUIT__642 = auto()
    GRIDWORKS__TSNAP1 = auto()
    GRIDWORKS__WATERTEMPHIGHPRECISION = auto()
    GRIDWORKS__SIMPM1 = auto()
    SCHNEIDERELECTRIC__IEM3455 = auto()
    GRIDWORKS__SIMBOOL30AMPRELAY = auto()
    OPENENERGY__EMONPI = auto()
    GRIDWORKS__SIMTSNAP1 = auto()
    ATLAS__EZFLO = auto()
    MAGNELAB__SCT0300050 = auto()
    YHDC__SCT013100 = auto()

    @classmethod
    def default(cls) -> "SpaceheatMakeModel000":
        return cls.UNKNOWNMAKE__UNKNOWNMODEL

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]


class MakeModelMap:
    @classmethod
    def type_to_local(cls, symbol: str) -> EnumMakeModel:
        if not SpaceheatMakeModel000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to SpaceheatMakeModel000 symbols"
            )
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, EnumMakeModel, EnumMakeModel.default())

    @classmethod
    def local_to_type(cls, make_model: EnumMakeModel) -> str:
        if not isinstance(make_model, EnumMakeModel):
            raise MpSchemaError(f"{make_model} must be of type {EnumMakeModel}")
        versioned_enum = as_enum(
            make_model, SpaceheatMakeModel000, SpaceheatMakeModel000.default()
        )
        return cls.versioned_enum_to_type_dict[versioned_enum]

    type_to_versioned_enum_dict: Dict[str, SpaceheatMakeModel000] = {
        "00000000": SpaceheatMakeModel000.UNKNOWNMAKE__UNKNOWNMODEL,
        "beb6d3fb": SpaceheatMakeModel000.EGAUGE__4030,
        "fabfa505": SpaceheatMakeModel000.NCD__PR814SPST,
        "acd93fb3": SpaceheatMakeModel000.ADAFRUIT__642,
        "d0178dc3": SpaceheatMakeModel000.GRIDWORKS__TSNAP1,
        "f8b497e8": SpaceheatMakeModel000.GRIDWORKS__WATERTEMPHIGHPRECISION,
        "076da322": SpaceheatMakeModel000.GRIDWORKS__SIMPM1,
        "d300635e": SpaceheatMakeModel000.SCHNEIDERELECTRIC__IEM3455,
        "e81d74a8": SpaceheatMakeModel000.GRIDWORKS__SIMBOOL30AMPRELAY,
        "c75d269f": SpaceheatMakeModel000.OPENENERGY__EMONPI,
        "3042c432": SpaceheatMakeModel000.GRIDWORKS__SIMTSNAP1,
        "d0b0e375": SpaceheatMakeModel000.ATLAS__EZFLO,
        "a8d9a70d": SpaceheatMakeModel000.MAGNELAB__SCT0300050,
        "08da3f7d": SpaceheatMakeModel000.YHDC__SCT013100,
    }

    versioned_enum_to_type_dict: Dict[SpaceheatMakeModel000, str] = {
        SpaceheatMakeModel000.UNKNOWNMAKE__UNKNOWNMODEL: "00000000",
        SpaceheatMakeModel000.EGAUGE__4030: "beb6d3fb",
        SpaceheatMakeModel000.NCD__PR814SPST: "fabfa505",
        SpaceheatMakeModel000.ADAFRUIT__642: "acd93fb3",
        SpaceheatMakeModel000.GRIDWORKS__TSNAP1: "d0178dc3",
        SpaceheatMakeModel000.GRIDWORKS__WATERTEMPHIGHPRECISION: "f8b497e8",
        SpaceheatMakeModel000.GRIDWORKS__SIMPM1: "076da322",
        SpaceheatMakeModel000.SCHNEIDERELECTRIC__IEM3455: "d300635e",
        SpaceheatMakeModel000.GRIDWORKS__SIMBOOL30AMPRELAY: "e81d74a8",
        SpaceheatMakeModel000.OPENENERGY__EMONPI: "c75d269f",
        SpaceheatMakeModel000.GRIDWORKS__SIMTSNAP1: "3042c432",
        SpaceheatMakeModel000.ATLAS__EZFLO: "d0b0e375",
        SpaceheatMakeModel000.MAGNELAB__SCT0300050: "a8d9a70d",
        SpaceheatMakeModel000.YHDC__SCT013100: "08da3f7d",
    }


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}")
    if len(x) != 5:
        raise ValueError(f"{v} split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError:
            raise ValueError(f"Words of {v} are not all hex")
    if len(x[0]) != 8:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[1]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[2]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[3]) != 4:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")
    if len(x[4]) != 12:
        raise ValueError(f"{v} word lengths not 8-4-4-4-12")


class GtBooleanActuatorCac(BaseModel):
    """Type for tracking Boolean Actuator ComponentAttributeClasses.

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and abstractions
    for managing relational device data. The Cac, or ComponentAttributeClass, is part of
    this structure.
    [More info](https://g-node-registry.readthedocs.io/en/latest/component-attribute-class.html).
    """

    ComponentAttributeClassId: str = Field(
        title="ComponentAttributeClassId",
    )
    MakeModel: EnumMakeModel = Field(
        title="MakeModel",
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    TypicalResponseTimeMs: int = Field(
        title="TypicalResponseTimeMs",
    )
    TypeName: Literal["gt.boolean.actuator.cac"] = "gt.boolean.actuator.cac"
    Version: str = "000"

    @validator("ComponentAttributeClassId")
    def _check_component_attribute_class_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"ComponentAttributeClassId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @validator("MakeModel")
    def _check_make_model(cls, v: EnumMakeModel) -> EnumMakeModel:
        return as_enum(v, EnumMakeModel, EnumMakeModel.UNKNOWNMAKE__UNKNOWNMODEL)

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        del d["MakeModel"]
        MakeModel = as_enum(self.MakeModel, EnumMakeModel, EnumMakeModel.default())
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_type(MakeModel)
        if d["DisplayName"] is None:
            del d["DisplayName"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class GtBooleanActuatorCac_Maker:
    type_name = "gt.boolean.actuator.cac"
    version = "000"

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: EnumMakeModel,
        display_name: Optional[str],
        typical_response_time_ms: int,
    ):

        self.tuple = GtBooleanActuatorCac(
            ComponentAttributeClassId=component_attribute_class_id,
            MakeModel=make_model,
            DisplayName=display_name,
            TypicalResponseTimeMs=typical_response_time_ms,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: GtBooleanActuatorCac) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtBooleanActuatorCac:
        """
        Given a serialized JSON type object, returns the Python class object
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtBooleanActuatorCac:
        d2 = dict(d)
        if "ComponentAttributeClassId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "MakeModelGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing MakeModelGtEnumSymbol")
        if d2["MakeModelGtEnumSymbol"] in SpaceheatMakeModel000SchemaEnum.symbols:
            d2["MakeModel"] = MakeModelMap.type_to_local(d2["MakeModelGtEnumSymbol"])
        else:
            d2["MakeModel"] = EnumMakeModel.default()
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "TypicalResponseTimeMs" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypicalResponseTimeMs")
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return GtBooleanActuatorCac(
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            MakeModel=d2["MakeModel"],
            DisplayName=d2["DisplayName"],
            TypicalResponseTimeMs=d2["TypicalResponseTimeMs"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: GtBooleanActuatorCac) -> BooleanActuatorCac:
        if t.ComponentAttributeClassId in BooleanActuatorCac.by_id.keys():
            dc = BooleanActuatorCac.by_id[t.ComponentAttributeClassId]
        else:
            dc = BooleanActuatorCac(
                component_attribute_class_id=t.ComponentAttributeClassId,
                make_model=t.MakeModel,
                display_name=t.DisplayName,
                typical_response_time_ms=t.TypicalResponseTimeMs,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: BooleanActuatorCac) -> GtBooleanActuatorCac:
        t = GtBooleanActuatorCac_Maker(
            component_attribute_class_id=dc.component_attribute_class_id,
            make_model=dc.make_model,
            display_name=dc.display_name,
            typical_response_time_ms=dc.typical_response_time_ms,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> BooleanActuatorCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: BooleanActuatorCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> BooleanActuatorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
