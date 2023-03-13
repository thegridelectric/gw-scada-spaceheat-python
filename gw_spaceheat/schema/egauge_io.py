"""Type egauge.io, version 000"""
import json
from typing import Any, Dict, Literal

from gwproto.errors import MpSchemaError
from pydantic import BaseModel, Field, validator

from schema.egauge_register_config import (
    EgaugeRegisterConfig,
    EgaugeRegisterConfig_Maker,
)
from schema.telemetry_reporting_config import (
    TelemetryReportingConfig,
    TelemetryReportingConfig_Maker,
)


class EgaugeIo(BaseModel):
    """Used for an eGauge meter's component information in a hardware layout.

    When the component associated to a PowerMeter ShNode has MakeModel EGAUGE__4030, there is a
    significant amount of configuration required to specify both what is read from the eGauge
    (input) and what is then sent up to the SCADA (output). This type handles that information.
    [More info](https://gridworks-protocol.readthedocs.io/en/latest/egauge-io.html).
    """

    InputConfig: EgaugeRegisterConfig = Field(
        title="InputConfig",
    )
    OutputConfig: TelemetryReportingConfig = Field(
        title="OutputConfig",
    )
    TypeName: Literal["egauge.io"] = "egauge.io"
    Version: str = "000"

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        d["InputConfig"] = self.InputConfig.as_dict()
        d["OutputConfig"] = self.OutputConfig.as_dict()
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class EgaugeIo_Maker:
    type_name = "egauge.io"
    version = "000"

    def __init__(
        self,
        input_config: EgaugeRegisterConfig,
        output_config: TelemetryReportingConfig,
    ):

        self.tuple = EgaugeIo(
            InputConfig=input_config,
            OutputConfig=output_config,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: EgaugeIo) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> EgaugeIo:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> EgaugeIo:
        d2 = dict(d)
        if "InputConfig" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing InputConfig")
        if not isinstance(d2["InputConfig"], dict):
            raise MpSchemaError(
                f"d['InputConfig'] {d2['InputConfig']} must be a EgaugeRegisterConfig!"
            )
        input_config = EgaugeRegisterConfig_Maker.dict_to_tuple(d2["InputConfig"])
        d2["InputConfig"] = input_config
        if "OutputConfig" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing OutputConfig")
        if not isinstance(d2["OutputConfig"], dict):
            raise MpSchemaError(
                f"d['OutputConfig'] {d2['OutputConfig']} must be a TelemetryReportingConfig!"
            )
        output_config = TelemetryReportingConfig_Maker.dict_to_tuple(d2["OutputConfig"])
        d2["OutputConfig"] = output_config
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return EgaugeIo(
            InputConfig=d2["InputConfig"],
            OutputConfig=d2["OutputConfig"],
            TypeName=d2["TypeName"],
            Version="000",
        )
