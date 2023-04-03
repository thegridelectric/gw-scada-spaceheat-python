"""Type electric.meter.cac.gt, version 000"""
import json
from enum import auto
from typing import Any, Dict, List, Literal, Optional

from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from enums import LocalCommInterface
from enums import MakeModel as EnumMakeModel
from enums import TelemetryName
from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError
from gwproto.message import as_enum
from pydantic import BaseModel, Field, validator


class SpaceheatTelemetryName000SchemaEnum:
    enum_name: str = "spaceheat.telemetry.name.000"
    symbols: List[str] = [
        "00000000",
        "af39eec9",
        "5a71d4b3",
        "c89d0ba1",
        "793505aa",
        "d70cce28",
        "ad19e79c",
        "329a68c0",
        "bb6fdd59",
        "e0bb014b",
        "337b8659",
        "0f627faa",
        "4c3f8c78",
    ]

    @classmethod
    def is_symbol(cls, candidate: str) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class SpaceheatTelemetryName000(StrEnum):
    Unknown = auto()
    PowerW = auto()
    RelayState = auto()
    WaterTempCTimes1000 = auto()
    WaterTempFTimes1000 = auto()
    GpmTimes100 = auto()
    CurrentRmsMicroAmps = auto()
    GallonsTimes100 = auto()
    VoltageRmsMilliVolts = auto()
    MilliWattHours = auto()
    FrequencyMicroHz = auto()
    AirTempCTimes1000 = auto()
    AirTempFTimes1000 = auto()

    @classmethod
    def default(cls) -> "SpaceheatTelemetryName000":
        return cls.Unknown

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]


class TelemetryNameMap:
    @classmethod
    def type_to_local(cls, symbol: str) -> TelemetryName:
        if not SpaceheatTelemetryName000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to SpaceheatTelemetryName000 symbols"
            )
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, TelemetryName, TelemetryName.default())

    @classmethod
    def local_to_type(cls, telemetry_name: TelemetryName) -> str:
        if not isinstance(telemetry_name, TelemetryName):
            raise MpSchemaError(f"{telemetry_name} must be of type {TelemetryName}")
        versioned_enum = as_enum(
            telemetry_name,
            SpaceheatTelemetryName000,
            SpaceheatTelemetryName000.default(),
        )
        return cls.versioned_enum_to_type_dict[versioned_enum]

    type_to_versioned_enum_dict: Dict[str, SpaceheatTelemetryName000] = {
        "00000000": SpaceheatTelemetryName000.Unknown,
        "af39eec9": SpaceheatTelemetryName000.PowerW,
        "5a71d4b3": SpaceheatTelemetryName000.RelayState,
        "c89d0ba1": SpaceheatTelemetryName000.WaterTempCTimes1000,
        "793505aa": SpaceheatTelemetryName000.WaterTempFTimes1000,
        "d70cce28": SpaceheatTelemetryName000.GpmTimes100,
        "ad19e79c": SpaceheatTelemetryName000.CurrentRmsMicroAmps,
        "329a68c0": SpaceheatTelemetryName000.GallonsTimes100,
        "bb6fdd59": SpaceheatTelemetryName000.VoltageRmsMilliVolts,
        "e0bb014b": SpaceheatTelemetryName000.MilliWattHours,
        "337b8659": SpaceheatTelemetryName000.FrequencyMicroHz,
        "0f627faa": SpaceheatTelemetryName000.AirTempCTimes1000,
        "4c3f8c78": SpaceheatTelemetryName000.AirTempFTimes1000,
    }

    versioned_enum_to_type_dict: Dict[SpaceheatTelemetryName000, str] = {
        SpaceheatTelemetryName000.Unknown: "00000000",
        SpaceheatTelemetryName000.PowerW: "af39eec9",
        SpaceheatTelemetryName000.RelayState: "5a71d4b3",
        SpaceheatTelemetryName000.WaterTempCTimes1000: "c89d0ba1",
        SpaceheatTelemetryName000.WaterTempFTimes1000: "793505aa",
        SpaceheatTelemetryName000.GpmTimes100: "d70cce28",
        SpaceheatTelemetryName000.CurrentRmsMicroAmps: "ad19e79c",
        SpaceheatTelemetryName000.GallonsTimes100: "329a68c0",
        SpaceheatTelemetryName000.VoltageRmsMilliVolts: "bb6fdd59",
        SpaceheatTelemetryName000.MilliWattHours: "e0bb014b",
        SpaceheatTelemetryName000.FrequencyMicroHz: "337b8659",
        SpaceheatTelemetryName000.AirTempCTimes1000: "0f627faa",
        SpaceheatTelemetryName000.AirTempFTimes1000: "4c3f8c78",
    }


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
    def type_to_local(cls, symbol: str) -> LocalCommInterface:
        if not LocalCommInterface000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to LocalCommInterface000 symbols"
            )
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, LocalCommInterface, LocalCommInterface.default())

    @classmethod
    def local_to_type(cls, local_comm_interface: LocalCommInterface) -> str:
        if not isinstance(local_comm_interface, LocalCommInterface):
            raise MpSchemaError(
                f"{local_comm_interface} must be of type {LocalCommInterface}"
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


class ElectricMeterCacGt(BaseModel):
    """Type for tracking  Electric Meter ComponentAttributeClasses.

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and abstractions for
    managing relational device data. The Cac, or ComponentAttributeClass, is part of this
    structure.
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
    TelemetryNameList: List[TelemetryName] = Field(
        title="TelenetryNames read by this power meter",
    )
    PollPeriodMs: int = Field(
        title="Shortest times to be used to poll power meter for new values",
    )
    Interface: LocalCommInterface = Field(
        title="Interface",
    )
    DefaultBaud: Optional[int] = Field(
        title="To be used when the comms method requires a baud rate",
        default=None,
    )
    TypeName: Literal["electric.meter.cac.gt"] = "electric.meter.cac.gt"
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

    @validator("TelemetryNameList")
    def _check_telemetry_name_list(
        cls, v: SpaceheatTelemetryName000
    ) -> [SpaceheatTelemetryName000]:
        if not isinstance(v, List):
            raise ValueError("TelemetryNameList must be a list!")
        enum_list = []
        for elt in v:
            enum_list.append(as_enum(elt, TelemetryName, TelemetryName.Unknown))
        return enum_list

    @validator("Interface")
    def _check_interface(cls, v: LocalCommInterface) -> LocalCommInterface:
        return as_enum(v, LocalCommInterface, LocalCommInterface.UNKNOWN)

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        del d["MakeModel"]
        MakeModel = as_enum(self.MakeModel, EnumMakeModel, EnumMakeModel.default())
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_type(MakeModel)
        if d["DisplayName"] is None:
            del d["DisplayName"]
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.TelemetryNameList:
            telemetry_name_list.append(TelemetryNameMap.local_to_type(elt))
        d["TelemetryNameList"] = telemetry_name_list
        del d["Interface"]
        Interface = as_enum(
            self.Interface, LocalCommInterface, LocalCommInterface.default()
        )
        d["InterfaceGtEnumSymbol"] = LocalCommInterfaceMap.local_to_type(Interface)
        if d["DefaultBaud"] is None:
            del d["DefaultBaud"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class ElectricMeterCacGt_Maker:
    type_name = "electric.meter.cac.gt"
    version = "000"

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: EnumMakeModel,
        display_name: Optional[str],
        telemetry_name_list: List[TelemetryName],
        poll_period_ms: int,
        interface: LocalCommInterface,
        default_baud: Optional[int],
    ):

        self.tuple = ElectricMeterCacGt(
            ComponentAttributeClassId=component_attribute_class_id,
            MakeModel=make_model,
            DisplayName=display_name,
            TelemetryNameList=telemetry_name_list,
            PollPeriodMs=poll_period_ms,
            Interface=interface,
            DefaultBaud=default_baud,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: ElectricMeterCacGt) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> ElectricMeterCacGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> ElectricMeterCacGt:
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
        if "TelemetryNameList" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TelemetryNameList")
        telemetry_name_list = []
        if not isinstance(d2["TelemetryNameList"], List):
            raise MpSchemaError("TelemetryNameList must be a List!")
        for elt in d2["TelemetryNameList"]:
            if elt in SpaceheatTelemetryName000SchemaEnum.symbols:
                v = TelemetryNameMap.type_to_local(elt)
            else:
                v = SpaceheatTelemetryName000.Unknown  #

            telemetry_name_list.append(v)
        d2["TelemetryNameList"] = telemetry_name_list
        if "PollPeriodMs" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing PollPeriodMs")
        if "InterfaceGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing InterfaceGtEnumSymbol")
        if d2["InterfaceGtEnumSymbol"] in LocalCommInterface000SchemaEnum.symbols:
            d2["Interface"] = LocalCommInterfaceMap.type_to_local(
                d2["InterfaceGtEnumSymbol"]
            )
        else:
            d2["Interface"] = LocalCommInterface.default()
        if "DefaultBaud" not in d2.keys():
            d2["DefaultBaud"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return ElectricMeterCacGt(
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            MakeModel=d2["MakeModel"],
            DisplayName=d2["DisplayName"],
            TelemetryNameList=d2["TelemetryNameList"],
            PollPeriodMs=d2["PollPeriodMs"],
            Interface=d2["Interface"],
            DefaultBaud=d2["DefaultBaud"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: ElectricMeterCacGt) -> ElectricMeterCac:
        if t.ComponentAttributeClassId in ElectricMeterCac.by_id.keys():
            dc = ElectricMeterCac.by_id[t.ComponentAttributeClassId]
        else:
            dc = ElectricMeterCac(
                component_attribute_class_id=t.ComponentAttributeClassId,
                make_model=t.MakeModel,
                display_name=t.DisplayName,
                telemetry_name_list=t.TelemetryNameList,
                poll_period_ms=t.PollPeriodMs,
                interface=t.Interface,
                default_baud=t.DefaultBaud,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ElectricMeterCac) -> ElectricMeterCacGt:
        t = ElectricMeterCacGt_Maker(
            component_attribute_class_id=dc.component_attribute_class_id,
            make_model=dc.make_model,
            display_name=dc.display_name,
            telemetry_name_list=dc.telemetry_name_list,
            poll_period_ms=dc.poll_period_ms,
            interface=dc.interface,
            default_baud=dc.default_baud,
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
