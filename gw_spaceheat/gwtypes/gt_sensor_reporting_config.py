"""Type gt.sensor.reporting.config, version 100"""
import json
import logging
from typing import Any, Dict, Literal, Optional

from gridworks.errors import SchemaError
from pydantic import BaseModel, Field

# enums
from enums import TelemetryName as EnumTelemetryName
from enums import Unit as EnumUnit

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GtSensorReportingConfig(BaseModel):
    """
    
    """

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
    Version: Literal["100"] = "100"

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        gt.sensor.reporting.config.100 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        gt.sensor.reporting.config.100 type. Unlike the standard python dict method,
        it makes the following substantive changes:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.
        """
        d = {
            key: value
            for key, value in self.dict(
                include=self.__fields_set__ | {"TypeName", "Version"}
            ).items()
            if value is not None
        }
        del d["TelemetryName"]
        d["TelemetryNameGtEnumSymbol"] = EnumTelemetryName.value_to_symbol(self.TelemetryName)
        del d["Unit"]
        d["UnitGtEnumSymbol"] = EnumUnit.value_to_symbol(self.Unit)
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the gt.sensor.reporting.config.100 representation.

        Instances in the class are python-native representations of gt.sensor.reporting.config.100
        objects, while the actual gt.sensor.reporting.config.100 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is GtSensorReportingConfig.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


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
        )

    @classmethod
    def tuple_to_type(cls, tuple: GtSensorReportingConfig) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> GtSensorReportingConfig:
        """
        Given a serialized JSON type object, returns the Python class object.
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise SchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise SchemaError(f"Deserializing <{t}> must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtSensorReportingConfig:
        """
        Deserialize a dictionary representation of a gt.sensor.reporting.config.100 message object
        into a GtSensorReportingConfig python object for internal use.

        This is the near-inverse of the GtSensorReportingConfig.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a SchemaError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           SchemaError: if the dict cannot be turned into a GtSensorReportingConfig object.

        Returns:
            GtSensorReportingConfig
        """
        d2 = dict(d)
        if "TelemetryNameGtEnumSymbol" not in d2.keys():
            raise SchemaError(f"TelemetryNameGtEnumSymbol missing from dict <{d2}>")
        value = EnumTelemetryName.symbol_to_value(d2["TelemetryNameGtEnumSymbol"])
        d2["TelemetryName"] = EnumTelemetryName(value)
        del d2["TelemetryNameGtEnumSymbol"]
        if "ReportingPeriodS" not in d2.keys():
            raise SchemaError(f"dict missing ReportingPeriodS: <{d2}>")
        if "SamplePeriodS" not in d2.keys():
            raise SchemaError(f"dict missing SamplePeriodS: <{d2}>")
        if "ReportOnChange" not in d2.keys():
            raise SchemaError(f"dict missing ReportOnChange: <{d2}>")
        if "Exponent" not in d2.keys():
            raise SchemaError(f"dict missing Exponent: <{d2}>")
        if "UnitGtEnumSymbol" not in d2.keys():
            raise SchemaError(f"UnitGtEnumSymbol missing from dict <{d2}>")
        value = EnumUnit.symbol_to_value(d2["UnitGtEnumSymbol"])
        d2["Unit"] = EnumUnit(value)
        del d2["UnitGtEnumSymbol"]
        if "TypeName" not in d2.keys():
            raise SchemaError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise SchemaError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "100":
            LOGGER.debug(
                f"Attempting to interpret gt.sensor.reporting.config version {d2['Version']} as version 100"
            )
            d2["Version"] = "100"
        return GtSensorReportingConfig(**d2)
