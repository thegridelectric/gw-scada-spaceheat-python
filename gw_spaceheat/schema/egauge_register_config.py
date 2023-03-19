"""Type egauge.register.config, version 000"""
import json
from typing import Any, Dict, Literal

from gwproto.errors import MpSchemaError
from pydantic import BaseModel, Field, validator


class EgaugeRegisterConfig(BaseModel):
    """
    Used to translate eGauge's Modbus Map

    This type captures the information provided by eGauge in its modbus csv map,
    when reading current, power, energy, voltage, frequency etc from an eGauge 4030.
    Used for example in the EGuage4030_PowerMeterDriver.
    """

    Address: int = Field(
        title="Address",
    )
    Name: str = Field(
        title="Name",
    )
    Description: str = Field(
        title="Description",
    )
    Type: str = Field(
        title="Type",
    )
    Denominator: int = Field(
        title="Denominator",
    )
    Unit: str = Field(
        title="Unit",
    )
    TypeName: Literal["egauge.register.config"] = "egauge.register.config"
    Version: str = "000"

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values())) # noqa


class EgaugeRegisterConfig_Maker:
    type_name = "egauge.register.config"
    version = "000"

    def __init__(
        self,
        address: int,
        name: str,
        description: str,
        type: str,
        denominator: int,
        unit: str,
    ):

        self.tuple = EgaugeRegisterConfig(
            Address=address,
            Name=name,
            Description=description,
            Type=type,
            Denominator=denominator,
            Unit=unit,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: EgaugeRegisterConfig) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> EgaugeRegisterConfig:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> EgaugeRegisterConfig:
        d2 = dict(d)
        if "Address" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Address")
        if "Name" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Name")
        if "Description" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Description")
        if "Type" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Type")
        if "Denominator" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Denominator")
        if "Unit" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing Unit")
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return EgaugeRegisterConfig(
            Address=d2["Address"],
            Name=d2["Name"],
            Description=d2["Description"],
            Type=d2["Type"],
            Denominator=d2["Denominator"],
            Unit=d2["Unit"],
            TypeName=d2["TypeName"],
            Version="000",
        )
