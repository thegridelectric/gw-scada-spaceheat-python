"""Type gt.powermeter.reporting.config, version 100"""
import json
import logging
from typing import Any, Dict, List, Literal, Optional

from gwproto.errors import SchemaError
from pydantic import BaseModel, Field

# sub-types
from gwtypes import TelemetryReportingConfig, TelemetryReportingConfig_Maker

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class GtPowermeterReportingConfig(BaseModel):
    """
    Power Meter Reporting Config.

    Contains data used to configure the power meters used to monitor and confirm the energy
    and power use of Transactive Loads. It is designed to be used, for example, by the SpaceheatNode
    actor in [Spaceheat SCADA code](https://github.com/thegridelectric/gw-scada-spaceheat-python)
    that is responsible for power metering.
    """

    ReportingPeriodS: int = Field(
        title="ReportingPeriodS",
    )
    ElectricalQuantityReportingConfigList: List[TelemetryReportingConfig] = Field(
        title="ElectricalQuantityReportingConfigList",
    )
    PollPeriodMs: int = Field(
        title="Poll Period in Milliseconds",
        description=(
            "Poll Period refers to the period of time between two readings by the local actor. "
            "This is in contrast to Capture Period, which refers to the period between readings "
            "that are sent up to the cloud (or otherwise saved for the long-term)."
            "[More info](https://gridworks-protocol.readthedocs.io/en/latest/data-polling-capturing-transmitting.rst)"
        ),
    )
    HwUid: Optional[str] = Field(
        title="Hardware Unique Id",
        default=None,
    )
    TypeName: Literal["gt.powermeter.reporting.config"] = "gt.powermeter.reporting.config"
    Version: Literal["100"] = "100"

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        gt.powermeter.reporting.config.100 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        gt.powermeter.reporting.config.100 type. Unlike the standard python dict method,
        it makes the following substantive changes:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.
        """
        d = {
            key: value
            for key, value in self.model_dump(
                include=self.model_fields_set | {"TypeName", "Version"}
            ).items()
            if value is not None
        }
        # Recursively calling as_dict()
        electrical_quantity_reporting_config_list = []
        for elt in self.ElectricalQuantityReportingConfigList:
            electrical_quantity_reporting_config_list.append(elt.as_dict())
        d["ElectricalQuantityReportingConfigList"] = electrical_quantity_reporting_config_list
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the gt.powermeter.reporting.config.100 representation.

        Instances in the class are python-native representations of gt.powermeter.reporting.config.100
        objects, while the actual gt.powermeter.reporting.config.100 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is GtPowermeterReportingConfig.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class GtPowermeterReportingConfig_Maker:
    type_name = "gt.powermeter.reporting.config"
    version = "100"

    def __init__(
        self,
        reporting_period_s: int,
        electrical_quantity_reporting_config_list: List[TelemetryReportingConfig],
        poll_period_ms: int,
        hw_uid: Optional[str],
    ):
        self.tuple = GtPowermeterReportingConfig(
            ReportingPeriodS=reporting_period_s,
            ElectricalQuantityReportingConfigList=electrical_quantity_reporting_config_list,
            PollPeriodMs=poll_period_ms,
            HwUid=hw_uid,
        )

    @classmethod
    def tuple_to_type(cls, tuple: GtPowermeterReportingConfig) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> GtPowermeterReportingConfig:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtPowermeterReportingConfig:
        """
        Deserialize a dictionary representation of a gt.powermeter.reporting.config.100 message object
        into a GtPowermeterReportingConfig python object for internal use.

        This is the near-inverse of the GtPowermeterReportingConfig.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a SchemaError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           SchemaError: if the dict cannot be turned into a GtPowermeterReportingConfig object.

        Returns:
            GtPowermeterReportingConfig
        """
        d2 = dict(d)
        if "ReportingPeriodS" not in d2.keys():
            raise SchemaError(f"dict missing ReportingPeriodS: <{d2}>")
        if "ElectricalQuantityReportingConfigList" not in d2.keys():
            raise SchemaError(f"dict missing ElectricalQuantityReportingConfigList: <{d2}>")
        if not isinstance(d2["ElectricalQuantityReportingConfigList"], List):
            raise SchemaError(f"ElectricalQuantityReportingConfigList <{d2['ElectricalQuantityReportingConfigList']}> must be a List!")
        electrical_quantity_reporting_config_list = []
        for elt in d2["ElectricalQuantityReportingConfigList"]:
            if not isinstance(elt, dict):
                raise SchemaError(f"ElectricalQuantityReportingConfigList <{d2['ElectricalQuantityReportingConfigList']}> must be a List of TelemetryReportingConfig types")
            t = TelemetryReportingConfig_Maker.dict_to_tuple(elt)
            electrical_quantity_reporting_config_list.append(t)
        d2["ElectricalQuantityReportingConfigList"] = electrical_quantity_reporting_config_list
        if "PollPeriodMs" not in d2.keys():
            raise SchemaError(f"dict missing PollPeriodMs: <{d2}>")
        if "TypeName" not in d2.keys():
            raise SchemaError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise SchemaError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "100":
            LOGGER.debug(
                f"Attempting to interpret gt.powermeter.reporting.config version {d2['Version']} as version 100"
            )
            d2["Version"] = "100"
        return GtPowermeterReportingConfig(**d2)
