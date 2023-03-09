"""Type gt.electric.meter.cac, version 000"""
import json
from enum import auto
from typing import Any, Dict, List, Literal, Optional

from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError
from gwproto.message import as_enum
from pydantic import BaseModel, Field, validator

from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from enums import LocalCommInterface as EnumLocalCommInterface
from enums import MakeModel as EnumMakeModel


class LocalCommInterface000SchemaEnum:
    enum_name: str = "local.comm.interface.000"
    symbols: List[str] = [
        "00000000",
        "9ec8bc49",
        "c1e7a955",
        "ae2d4cd8",
        "a6a4ac9f",
        "efc144cd",
        "46ac6589",
        "653c73b8",
        "0843a726",
    ]

    @classmethod
    def is_symbol(cls, candidate: str) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class LocalCommInterface000(StrEnum):
    UNKNOWN = auto()
    I2C = auto()
    ETHERNET = auto()
    ONEWIRE = auto()
    RS485 = auto()
    SIMRABBIT = auto()
    WIFI = auto()
    ANALOG_4_20_MA = auto()
    RS232 = auto()

    @classmethod
    def default(cls) -> "LocalCommInterface000":
        return cls.UNKNOWN

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]


class LocalCommInterfaceMap:
    @classmethod
    def type_to_local(cls, symbol: str) -> EnumLocalCommInterface:
        if not LocalCommInterface000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to LocalCommInterface000 symbols"
            )
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(
            versioned_enum, EnumLocalCommInterface, EnumLocalCommInterface.default()
        )

    @classmethod
    def local_to_type(cls, local_comm_interface: EnumLocalCommInterface) -> str:
        if not isinstance(local_comm_interface, EnumLocalCommInterface):
            raise MpSchemaError(
                f"{local_comm_interface} must be of type {EnumLocalCommInterface}"
            )
        versioned_enum = as_enum(
            local_comm_interface, LocalCommInterface000, LocalCommInterface000.default()
        )
        return cls.versioned_enum_to_type_dict[versioned_enum]

    type_to_versioned_enum_dict: Dict[str, LocalCommInterface000] = {
        "00000000": LocalCommInterface000.UNKNOWN,
        "9ec8bc49": LocalCommInterface000.I2C,
        "c1e7a955": LocalCommInterface000.ETHERNET,
        "ae2d4cd8": LocalCommInterface000.ONEWIRE,
        "a6a4ac9f": LocalCommInterface000.RS485,
        "efc144cd": LocalCommInterface000.SIMRABBIT,
        "46ac6589": LocalCommInterface000.WIFI,
        "653c73b8": LocalCommInterface000.ANALOG_4_20_MA,
        "0843a726": LocalCommInterface000.RS232,
    }

    versioned_enum_to_type_dict: Dict[LocalCommInterface000, str] = {
        LocalCommInterface000.UNKNOWN: "00000000",
        LocalCommInterface000.I2C: "9ec8bc49",
        LocalCommInterface000.ETHERNET: "c1e7a955",
        LocalCommInterface000.ONEWIRE: "ae2d4cd8",
        LocalCommInterface000.RS485: "a6a4ac9f",
        LocalCommInterface000.SIMRABBIT: "efc144cd",
        LocalCommInterface000.WIFI: "46ac6589",
        LocalCommInterface000.ANALOG_4_20_MA: "653c73b8",
        LocalCommInterface000.RS232: "0843a726",
    }


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


class GtElectricMeterCac(BaseModel):
    """Type for tracking Electric Meter ComponentAttributeClasses

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and abstractions
    for managing relational device data. The Cac, or ComponentAttributeClass, is part of
    this structure.

    [More info](https://g-node-registry.readthedocs.io/en/latest/component-attribute-class.html)"""

    ComponentAttributeClassId: str = Field(
        title="ComponentAttributeClassId",
    )
    MakeModel: EnumMakeModel = Field(
        title="MakeModel",
    )
    LocalCommInterface: EnumLocalCommInterface = Field(
        title="LocalCommInterface",
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    DefaultBaud: Optional[int] = Field(
        title="DefaultBaud",
        default=None,
    )
    UpdatePeriodMs: Optional[int] = Field(
        title="UpdatePeriodMs",
        default=None,
    )
    TypeName: Literal["gt.electric.meter.cac"] = "gt.electric.meter.cac"
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

    @validator("LocalCommInterface")
    def _check_local_comm_interface(
        cls, v: EnumLocalCommInterface
    ) -> EnumLocalCommInterface:
        return as_enum(v, EnumLocalCommInterface, EnumLocalCommInterface.UNKNOWN)

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        del d["MakeModel"]
        MakeModel = as_enum(self.MakeModel, EnumMakeModel, EnumMakeModel.default())
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_type(MakeModel)
        del d["LocalCommInterface"]
        LocalCommInterface = as_enum(
            self.LocalCommInterface,
            EnumLocalCommInterface,
            EnumLocalCommInterface.default(),
        )
        d["LocalCommInterfaceGtEnumSymbol"] = LocalCommInterfaceMap.local_to_type(
            LocalCommInterface
        )
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["DefaultBaud"] is None:
            del d["DefaultBaud"]
        if d["UpdatePeriodMs"] is None:
            del d["UpdatePeriodMs"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class GtElectricMeterCac_Maker:
    type_name = "gt.electric.meter.cac"
    version = "000"

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: EnumMakeModel,
        local_comm_interface: EnumLocalCommInterface,
        display_name: Optional[str],
        default_baud: Optional[int],
        update_period_ms: Optional[int],
    ):

        self.tuple = GtElectricMeterCac(
            ComponentAttributeClassId=component_attribute_class_id,
            MakeModel=make_model,
            LocalCommInterface=local_comm_interface,
            DisplayName=display_name,
            DefaultBaud=default_baud,
            UpdatePeriodMs=update_period_ms,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: GtElectricMeterCac) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtElectricMeterCac:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtElectricMeterCac:
        d2 = dict(d)
        if "ComponentAttributeClassId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "MakeModelGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing MakeModelGtEnumSymbol")
        if d2["MakeModelGtEnumSymbol"] in SpaceheatMakeModel000SchemaEnum.symbols:
            d2["MakeModel"] = MakeModelMap.type_to_local(d2["MakeModelGtEnumSymbol"])
        else:
            d2["MakeModel"] = EnumMakeModel.default()
        if "LocalCommInterfaceGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing LocalCommInterfaceGtEnumSymbol")
        if (
            d2["LocalCommInterfaceGtEnumSymbol"]
            in LocalCommInterface000SchemaEnum.symbols
        ):
            d2["LocalCommInterface"] = LocalCommInterfaceMap.type_to_local(
                d2["LocalCommInterfaceGtEnumSymbol"]
            )
        else:
            d2["LocalCommInterface"] = EnumLocalCommInterface.default()
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "DefaultBaud" not in d2.keys():
            d2["DefaultBaud"] = None
        if "UpdatePeriodMs" not in d2.keys():
            d2["UpdatePeriodMs"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return GtElectricMeterCac(
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            MakeModel=d2["MakeModel"],
            LocalCommInterface=d2["LocalCommInterface"],
            DisplayName=d2["DisplayName"],
            DefaultBaud=d2["DefaultBaud"],
            UpdatePeriodMs=d2["UpdatePeriodMs"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: GtElectricMeterCac) -> ElectricMeterCac:
        if t.ComponentAttributeClassId in ElectricMeterCac.by_id.keys():
            dc = ElectricMeterCac.by_id[t.ComponentAttributeClassId]
        else:
            dc = ElectricMeterCac(
                component_attribute_class_id=t.ComponentAttributeClassId,
                make_model=t.MakeModel,
                local_comm_interface=t.LocalCommInterface,
                display_name=t.DisplayName,
                default_baud=t.DefaultBaud,
                update_period_ms=t.UpdatePeriodMs,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricMeterCac) -> GtElectricMeterCac:
        t = GtElectricMeterCac_Maker(
            component_attribute_class_id=dc.component_attribute_class_id,
            make_model=dc.make_model,
            local_comm_interface=dc.local_comm_interface,
            display_name=dc.display_name,
            default_baud=dc.default_baud,
            update_period_ms=dc.update_period_ms,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ElectricMeterCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ElectricMeterCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> ElectricMeterCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
