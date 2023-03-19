"""Type gt.sensor.reporting.config, version 100"""
import json
from enum import auto
from typing import Any, Dict, List, Literal, Optional

from enums import TelemetryName as EnumTelemetryName
from enums import Unit as EnumUnit
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
    def type_to_local(cls, symbol: str) -> EnumTelemetryName:
        if not SpaceheatTelemetryName000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to SpaceheatTelemetryName000 symbols"
            )
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, EnumTelemetryName, EnumTelemetryName.default())

    @classmethod
    def local_to_type(cls, telemetry_name: EnumTelemetryName) -> str:
        if not isinstance(telemetry_name, EnumTelemetryName):
            raise MpSchemaError(f"{telemetry_name} must be of type {EnumTelemetryName}")
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
    def type_to_local(cls, symbol: str) -> EnumUnit:
        if not SpaceheatUnit000SchemaEnum.is_symbol(symbol):
            raise MpSchemaError(f"{symbol} must belong to SpaceheatUnit000 symbols")
        versioned_enum = cls.type_to_versioned_enum_dict[symbol]
        return as_enum(versioned_enum, EnumUnit, EnumUnit.default())

    @classmethod
    def local_to_type(cls, unit: EnumUnit) -> str:
        if not isinstance(unit, EnumUnit):
            raise MpSchemaError(f"{unit} must be of type {EnumUnit}")
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


class GtSensorReportingConfig(BaseModel):
    """ """

    TelemetryName: EnumTelemetryName = Field(
        title="TelemetryName",
    )
    ReportingPeriodS: int = Field(
        title="ReportingPeriodS",
    )
    SamplePeriodS: int = Field(
        title="SamplePeriodS",
    )
    ReportOnChange: bool = Field(
        title="ReportOnChange",
    )
    Exponent: int = Field(
        title="Exponent",
    )
    Unit: EnumUnit = Field(
        title="Unit",
    )
    AsyncReportThreshold: Optional[float] = Field(
        title="AsyncReportThreshold",
        default=None,
    )
    TypeName: Literal["gt.sensor.reporting.config"] = "gt.sensor.reporting.config"
    Version: str = "100"

    @validator("TelemetryName")
    def _check_telemetry_name(cls, v: EnumTelemetryName) -> EnumTelemetryName:
        return as_enum(v, EnumTelemetryName, EnumTelemetryName.Unknown)

    @validator("Unit")
    def _check_unit(cls, v: EnumUnit) -> EnumUnit:
        return as_enum(v, EnumUnit, EnumUnit.Unknown)

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        del d["TelemetryName"]
        TelemetryName = as_enum(
            self.TelemetryName, EnumTelemetryName, EnumTelemetryName.default()
        )
        d["TelemetryNameGtEnumSymbol"] = TelemetryNameMap.local_to_type(TelemetryName)
        del d["Unit"]
        Unit = as_enum(self.Unit, EnumUnit, EnumUnit.default())
        d["UnitGtEnumSymbol"] = UnitMap.local_to_type(Unit)
        if d["AsyncReportThreshold"] is None:
            del d["AsyncReportThreshold"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values())) # noqa


class GtSensorReportingConfig_Maker:
    type_name = "gt.sensor.reporting.config"
    version = "100"

    def __init__(
        self,
        telemetry_name: EnumTelemetryName,
        reporting_period_s: int,
        sample_period_s: int,
        report_on_change: bool,
        exponent: int,
        unit: EnumUnit,
        async_report_threshold: Optional[float],
    ):

        self.tuple = GtSensorReportingConfig(
            TelemetryName=telemetry_name,
            ReportingPeriodS=reporting_period_s,
            SamplePeriodS=sample_period_s,
            ReportOnChange=report_on_change,
            Exponent=exponent,
            Unit=unit,
            AsyncReportThreshold=async_report_threshold,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: GtSensorReportingConfig) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtSensorReportingConfig:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtSensorReportingConfig:
        d2 = dict(d)
        if "TelemetryNameGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TelemetryNameGtEnumSymbol")
        if (
            d2["TelemetryNameGtEnumSymbol"]
            in SpaceheatTelemetryName000SchemaEnum.symbols
        ):
            d2["TelemetryName"] = TelemetryNameMap.type_to_local(
                d2["TelemetryNameGtEnumSymbol"]
            )
        else:
            d2["TelemetryName"] = EnumTelemetryName.default()
        if "ReportingPeriodS" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ReportingPeriodS")
        if "SamplePeriodS" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing SamplePeriodS")
        if "ReportOnChange" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ReportOnChange")
        if "Exponent" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Exponent")
        if "UnitGtEnumSymbol" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing UnitGtEnumSymbol")
        if d2["UnitGtEnumSymbol"] in SpaceheatUnit000SchemaEnum.symbols:
            d2["Unit"] = UnitMap.type_to_local(d2["UnitGtEnumSymbol"])
        else:
            d2["Unit"] = EnumUnit.default()
        if "AsyncReportThreshold" not in d2.keys():
            d2["AsyncReportThreshold"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return GtSensorReportingConfig(
            TelemetryName=d2["TelemetryName"],
            ReportingPeriodS=d2["ReportingPeriodS"],
            SamplePeriodS=d2["SamplePeriodS"],
            ReportOnChange=d2["ReportOnChange"],
            Exponent=d2["Exponent"],
            Unit=d2["Unit"],
            AsyncReportThreshold=d2["AsyncReportThreshold"],
            TypeName=d2["TypeName"],
            Version="100",
        )
