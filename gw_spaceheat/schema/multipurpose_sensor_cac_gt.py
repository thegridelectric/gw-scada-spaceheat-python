"""Type multipurpose.sensor.cac.gt, version 000"""
import json
from enum import auto
from typing import Any, Dict, List, Literal, Optional

from data_classes.cacs.multipurpose_sensor_cac import MultipurposeSensorCac
from enums import MakeModel as EnumMakeModel
from enums import TelemetryName, Unit
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


class SpaceheatUnit000SchemaEnum:
    enum_name: str = "spaceheat.unit.000"
    symbols: List[str] = [
        "00000000",
        "ec972387",
        "f459a9c3",
        "ec14bd47",
        "7d8832f8",
        "b4580361",
        "d66f1622",
        "a969ac7c",
        "e5d7555c",
        "8e123a26",
    ]

    @classmethod
    def is_symbol(cls, candidate: str) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class SpaceheatUnit000(StrEnum):
    Unknown = auto()
    Unitless = auto()
    W = auto()
    Celcius = auto()
    Fahrenheit = auto()
    Gpm = auto()
    WattHours = auto()
    AmpsRms = auto()
    VoltsRms = auto()
    Gallons = auto()

    @classmethod
    def default(cls) -> "SpaceheatUnit000":
        return cls.Unknown

    @classmethod
    def values(cls) -> List[str]:
        return [elt.value for elt in cls]


class UnitMap:
    @classmethod
    def type_to_local(cls, symbol: str) -> Unit:
        if not SpaceheatUnit000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(f"{symbol} must belong to SpaceheatUnit000 symbols")
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, Unit, Unit.default())

    @classmethod
    def local_to_type(cls, unit: Unit) -> str:
        if not isinstance(unit, Unit):
            raise MpSchemaError(f"{unit} must be of type {Unit}")
        versioned_enum = as_enum(unit, SpaceheatUnit000, SpaceheatUnit000.default())
        return cls.versioned_enum_to_type_dict[versioned_enum]

    type_to_versioned_enum_dict: Dict[str, SpaceheatUnit000] = {
        "00000000": SpaceheatUnit000.Unknown,
        "ec972387": SpaceheatUnit000.Unitless,
        "f459a9c3": SpaceheatUnit000.W,
        "ec14bd47": SpaceheatUnit000.Celcius,
        "7d8832f8": SpaceheatUnit000.Fahrenheit,
        "b4580361": SpaceheatUnit000.Gpm,
        "d66f1622": SpaceheatUnit000.WattHours,
        "a969ac7c": SpaceheatUnit000.AmpsRms,
        "e5d7555c": SpaceheatUnit000.VoltsRms,
        "8e123a26": SpaceheatUnit000.Gallons,
    }

    versioned_enum_to_type_dict: Dict[SpaceheatUnit000, str] = {
        SpaceheatUnit000.Unknown: "00000000",
        SpaceheatUnit000.Unitless: "ec972387",
        SpaceheatUnit000.W: "f459a9c3",
        SpaceheatUnit000.Celcius: "ec14bd47",
        SpaceheatUnit000.Fahrenheit: "7d8832f8",
        SpaceheatUnit000.Gpm: "b4580361",
        SpaceheatUnit000.WattHours: "d66f1622",
        SpaceheatUnit000.AmpsRms: "a969ac7c",
        SpaceheatUnit000.VoltsRms: "e5d7555c",
        SpaceheatUnit000.Gallons: "8e123a26",
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


class MultipurposeSensorCacGt(BaseModel):
    """Type for tracking Multipuprose Sensor ComponentAttributeClasses.

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and
    abstractions for managing relational device data. The Cac, or ComponentAttributeClass,
    is part of this structure.

    [More info](https://g-node-registry.readthedocs.io/en/latest/component-attribute-class.html).
    """

    ComponentAttributeClassId: str = Field(
        title="ComponentAttributeClassId",
    )
    MakeModel: EnumMakeModel = Field(
        title="MakeModel",
    )
    PollPeriodMs: int = Field(
        title="PollPeriodMs",
    )
    Exponent: int = Field(
        title="Exponent",
    )
    TempUnit: Unit = Field(
        title="TempUnit",
    )
    TelemetryNameList: List[TelemetryName] = Field(
        title="TelemetryNameList",
    )
    MaxThermistors: Optional[int] = Field(
        title="MaxThermistors",
        default=None,
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    CommsMethod: Optional[str] = Field(
        title="CommsMethod",
        default=None,
    )
    TypeName: Literal["multipurpose.sensor.cac.gt"] = "multipurpose.sensor.cac.gt"
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

    @validator("TempUnit")
    def _check_temp_unit(cls, v: Unit) -> Unit:
        return as_enum(v, Unit, Unit.Unknown)

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

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        del d["MakeModel"]
        MakeModel = as_enum(self.MakeModel, EnumMakeModel, EnumMakeModel.default())
        d["MakeModelGtEnumSymbol"] = MakeModelMap.local_to_type(MakeModel)
        del d["TempUnit"]
        TempUnit = as_enum(self.TempUnit, Unit, Unit.default())
        d["TempUnitGtEnumSymbol"] = UnitMap.local_to_type(TempUnit)
        del d["TelemetryNameList"]
        telemetry_name_list = []
        for elt in self.TelemetryNameList:
            telemetry_name_list.append(TelemetryNameMap.local_to_type(elt))
        d["TelemetryNameList"] = telemetry_name_list
        if d["MaxThermistors"] is None:
            del d["MaxThermistors"]
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["CommsMethod"] is None:
            del d["CommsMethod"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class MultipurposeSensorCacGt_Maker:
    type_name = "multipurpose.sensor.cac.gt"
    version = "000"

    def __init__(
        self,
        component_attribute_class_id: str,
        make_model: EnumMakeModel,
        poll_period_ms: int,
        exponent: int,
        temp_unit: Unit,
        telemetry_name_list: List[TelemetryName],
        max_thermistors: Optional[int],
        display_name: Optional[str],
        comms_method: Optional[str],
    ):

        self.tuple = MultipurposeSensorCacGt(
            ComponentAttributeClassId=component_attribute_class_id,
            MakeModel=make_model,
            PollPeriodMs=poll_period_ms,
            Exponent=exponent,
            TempUnit=temp_unit,
            TelemetryNameList=telemetry_name_list,
            MaxThermistors=max_thermistors,
            DisplayName=display_name,
            CommsMethod=comms_method,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: MultipurposeSensorCacGt) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> MultipurposeSensorCacGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> MultipurposeSensorCacGt:
        d2 = dict(d)
        if "ComponentAttributeClassId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "MakeModelGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing MakeModelGtEnumSymbol")
        if d2["MakeModelGtEnumSymbol"] in SpaceheatMakeModel000SchemaEnum.symbols:
            d2["MakeModel"] = MakeModelMap.type_to_local(d2["MakeModelGtEnumSymbol"])
        else:
            d2["MakeModel"] = EnumMakeModel.default()
        if "PollPeriodMs" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing PollPeriodMs")
        if "Exponent" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Exponent")
        if "TempUnitGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TempUnitGtEnumSymbol")
        if d2["TempUnitGtEnumSymbol"] in SpaceheatUnit000SchemaEnum.symbols:
            d2["TempUnit"] = UnitMap.type_to_local(d2["TempUnitGtEnumSymbol"])
        else:
            d2["TempUnit"] = Unit.default()
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
        if "MaxThermistors" not in d2.keys():
            d2["MaxThermistors"] = None
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "CommsMethod" not in d2.keys():
            d2["CommsMethod"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return MultipurposeSensorCacGt(
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            MakeModel=d2["MakeModel"],
            PollPeriodMs=d2["PollPeriodMs"],
            Exponent=d2["Exponent"],
            TempUnit=d2["TempUnit"],
            TelemetryNameList=d2["TelemetryNameList"],
            MaxThermistors=d2["MaxThermistors"],
            DisplayName=d2["DisplayName"],
            CommsMethod=d2["CommsMethod"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: MultipurposeSensorCacGt) -> MultipurposeSensorCac:
        if t.ComponentAttributeClassId in MultipurposeSensorCac.by_id.keys():
            dc = MultipurposeSensorCac.by_id[t.ComponentAttributeClassId]
        else:
            dc = MultipurposeSensorCac(
                component_attribute_class_id=t.ComponentAttributeClassId,
                make_model=t.MakeModel,
                poll_period_ms=t.PollPeriodMs,
                exponent=t.Exponent,
                temp_unit=t.TempUnit,
                telemetry_name_list=t.TelemetryNameList,
                max_thermistors=t.MaxThermistors,
                display_name=t.DisplayName,
                comms_method=t.CommsMethod,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: MultipurposeSensorCac) -> MultipurposeSensorCacGt:
        t = MultipurposeSensorCacGt_Maker(
            component_attribute_class_id=dc.component_attribute_class_id,
            make_model=dc.make_model,
            poll_period_ms=dc.poll_period_ms,
            exponent=dc.exponent,
            temp_unit=dc.temp_unit,
            telemetry_name_list=dc.telemetry_name_list,
            max_thermistors=dc.max_thermistors,
            display_name=dc.display_name,
            comms_method=dc.comms_method,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> MultipurposeSensorCac:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: MultipurposeSensorCac) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> MultipurposeSensorCac:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
