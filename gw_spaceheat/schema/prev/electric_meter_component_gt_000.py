"""Type electric.meter.component.gt, version 000"""
import json
from typing import Any, Dict, Literal, Optional

from gwproto.data_classes.components.electric_meter_component import \
    ElectricMeterComponent
from gwproto.errors import SchemaError
from pydantic import BaseModel, Field, validator


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


class ElectricMeterComponentGt000(BaseModel):
    """Type for tracking Electric Meter Components.

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and abstractions
    for managing relational device data. The Component associated to a SpaceheatNode
    is part of this structure.
    [More info](https://g-node-registry.readthedocs.io/en/latest/component.html).
    """

    ComponentId: str = Field(
        title="ComponentId",
    )
    ComponentAttributeClassId: str = Field(
        title="ComponentAttributeClassId",
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    HwUid: Optional[str] = Field(
        title="HwUid",
        default=None,
    )
    ModbusHost: Optional[str] = Field(
        title="ModbusHost",
        default=None,
    )
    ModbusPort: Optional[int] = Field(
        title="ModbusPort",
        default=None,
    )
    ModbusPowerRegister: Optional[int] = Field(
        title="ModbusPowerRegister",
        default=None,
    )
    ModbusHwUidRegister: Optional[int] = Field(
        title="ModbusHwUidRegister",
        default=None,
    )
    TypeName: Literal["electric.meter.component.gt"] = "electric.meter.component.gt"
    Version: str = "000"

    @validator("ComponentId")
    def _check_component_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"ComponentId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @validator("ComponentAttributeClassId")
    def _check_component_attribute_class_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"ComponentAttributeClassId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["HwUid"] is None:
            del d["HwUid"]
        if d["ModbusHost"] is None:
            del d["ModbusHost"]
        if d["ModbusPort"] is None:
            del d["ModbusPort"]
        if d["ModbusPowerRegister"] is None:
            del d["ModbusPowerRegister"]
        if d["ModbusHwUidRegister"] is None:
            del d["ModbusHwUidRegister"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class ElectricMeterComponentGt000_Maker:
    type_name = "electric.meter.component.gt"
    version = "000"

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        display_name: Optional[str],
        hw_uid: Optional[str],
        modbus_host: Optional[str],
        modbus_port: Optional[int],
        modbus_power_register: Optional[int],
        modbus_hw_uid_register: Optional[int],
    ):

        self.tuple = ElectricMeterComponentGt000(
            ComponentId=component_id,
            ComponentAttributeClassId=component_attribute_class_id,
            DisplayName=display_name,
            HwUid=hw_uid,
            ModbusHost=modbus_host,
            ModbusPort=modbus_port,
            ModbusPowerRegister=modbus_power_register,
            ModbusHwUidRegister=modbus_hw_uid_register,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: ElectricMeterComponentGt000) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> ElectricMeterComponentGt000:
        """
        Given a serialized JSON type object, returns the Python class object
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise SchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise SchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> ElectricMeterComponentGt000:
        d2 = dict(d)
        if "ComponentId" not in d2.keys():
            raise SchemaError(f"dict {d2} missing ComponentId")
        if "ComponentAttributeClassId" not in d2.keys():
            raise SchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "HwUid" not in d2.keys():
            d2["HwUid"] = None
        if "ModbusHost" not in d2.keys():
            d2["ModbusHost"] = None
        if "ModbusPort" not in d2.keys():
            d2["ModbusPort"] = None
        if "ModbusPowerRegister" not in d2.keys():
            d2["ModbusPowerRegister"] = None
        if "ModbusHwUidRegister" not in d2.keys():
            d2["ModbusHwUidRegister"] = None
        if "TypeName" not in d2.keys():
            raise SchemaError(f"dict {d2} missing TypeName")

        return ElectricMeterComponentGt000(
            ComponentId=d2["ComponentId"],
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            DisplayName=d2["DisplayName"],
            HwUid=d2["HwUid"],
            ModbusHost=d2["ModbusHost"],
            ModbusPort=d2["ModbusPort"],
            ModbusPowerRegister=d2["ModbusPowerRegister"],
            ModbusHwUidRegister=d2["ModbusHwUidRegister"],
            TypeName=d2["TypeName"],
            Version="000",
        )
