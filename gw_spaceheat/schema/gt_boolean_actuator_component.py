"""Type gt.boolean.actuator.component, version 000"""
import json
from typing import Any, Dict, Literal, Optional

from gwproto.errors import MpSchemaError
from pydantic import BaseModel, Field, validator

from data_classes.components.boolean_actuator_component import BooleanActuatorComponent


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


class GtBooleanActuatorComponent(BaseModel):
    """Type for tracking Boolean ActuatorComponents

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and
    abstractionsfor managing relational device data. The Component associated
    to a SpaceheatNode is part of this structure.

    [More info](https://g-node-registry.readthedocs.io/en/latest/component.html)
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
    Gpio: Optional[int] = Field(
        title="Gpio",
        default=None,
    )
    HwUid: Optional[str] = Field(
        title="HwUid",
        default=None,
    )
    TypeName: Literal["gt.boolean.actuator.component"] = "gt.boolean.actuator.component"
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
        if d["Gpio"] is None:
            del d["Gpio"]
        if d["HwUid"] is None:
            del d["HwUid"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class GtBooleanActuatorComponent_Maker:
    type_name = "gt.boolean.actuator.component"
    version = "000"

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        display_name: Optional[str],
        gpio: Optional[int],
        hw_uid: Optional[str],
    ):

        self.tuple = GtBooleanActuatorComponent(
            ComponentId=component_id,
            ComponentAttributeClassId=component_attribute_class_id,
            DisplayName=display_name,
            Gpio=gpio,
            HwUid=hw_uid,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: GtBooleanActuatorComponent) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtBooleanActuatorComponent:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> GtBooleanActuatorComponent:
        d2 = dict(d)
        if "ComponentId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentId")
        if "ComponentAttributeClassId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "Gpio" not in d2.keys():
            d2["Gpio"] = None
        if "HwUid" not in d2.keys():
            d2["HwUid"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return GtBooleanActuatorComponent(
            ComponentId=d2["ComponentId"],
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            DisplayName=d2["DisplayName"],
            Gpio=d2["Gpio"],
            HwUid=d2["HwUid"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: GtBooleanActuatorComponent) -> BooleanActuatorComponent:
        if t.ComponentId in BooleanActuatorComponent.by_id.keys():
            dc = BooleanActuatorComponent.by_id[t.ComponentId]
        else:
            dc = BooleanActuatorComponent(
                component_id=t.ComponentId,
                component_attribute_class_id=t.ComponentAttributeClassId,
                display_name=t.DisplayName,
                gpio=t.Gpio,
                hw_uid=t.HwUid,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: BooleanActuatorComponent) -> GtBooleanActuatorComponent:
        t = GtBooleanActuatorComponent_Maker(
            component_id=dc.component_id,
            component_attribute_class_id=dc.component_attribute_class_id,
            display_name=dc.display_name,
            gpio=dc.gpio,
            hw_uid=dc.hw_uid,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> BooleanActuatorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: BooleanActuatorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> BooleanActuatorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
