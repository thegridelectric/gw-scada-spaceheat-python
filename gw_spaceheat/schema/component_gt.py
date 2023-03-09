"""Type component.gt, version 000"""
import json
from typing import Any, Dict, Literal, Optional

from data_classes.component import Component
from gwproto.errors import MpSchemaError
from pydantic import BaseModel, Field, validator
from schema.component_attribute_class_gt import (
    ComponentAttributeClassGt, ComponentAttributeClassGt_Maker)


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


class ComponentGt(BaseModel):
    """ """

    ComponentId: str = Field(
        title="ComponentId",
    )
    ComponentAttributeClass: ComponentAttributeClassGt = Field(
        title="ComponentAttributeClass",
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    HwUid: Optional[str] = Field(
        title="HwUid",
        default=None,
    )
    TypeName: Literal["component.gt"] = "component.gt"
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

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        d["ComponentAttributeClass"] = self.ComponentAttributeClass.as_dict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        if d["HwUid"] is None:
            del d["HwUid"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class ComponentGt_Maker:
    type_name = "component.gt"
    version = "000"

    def __init__(
        self,
        component_id: str,
        component_attribute_class: ComponentAttributeClassGt,
        display_name: Optional[str],
        hw_uid: Optional[str],
    ):

        self.tuple = ComponentGt(
            ComponentId=component_id,
            ComponentAttributeClass=component_attribute_class,
            DisplayName=display_name,
            HwUid=hw_uid,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: ComponentGt) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> ComponentGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> ComponentGt:
        d2 = dict(d)
        if "ComponentId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentId")
        if "ComponentAttributeClass" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClass")
        if not isinstance(d2["ComponentAttributeClass"], dict):
            raise MpSchemaError(
                f"d['ComponentAttributeClass'] {d2['ComponentAttributeClass']} must be a ComponentAttributeClassGt!"
            )
        component_attribute_class = ComponentAttributeClassGt_Maker.dict_to_tuple(
            d2["ComponentAttributeClass"]
        )
        d2["ComponentAttributeClass"] = component_attribute_class
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "HwUid" not in d2.keys():
            d2["HwUid"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return ComponentGt(
            ComponentId=d2["ComponentId"],
            ComponentAttributeClass=d2["ComponentAttributeClass"],
            DisplayName=d2["DisplayName"],
            HwUid=d2["HwUid"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: ComponentGt) -> Component:
        if t.ComponentId in Component.by_id.keys():
            dc = Component.by_id[t.ComponentId]
        else:
            dc = Component(
                component_id=t.ComponentId,
                component_attribute_class=ComponentAttributeClassGt_Maker.tuple_to_dc(
                    t.ComponentAttributeClass
                ),
                display_name=t.DisplayName,
                hw_uid=t.HwUid,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: Component) -> ComponentGt:
        t = ComponentGt_Maker(
            component_id=dc.component_id,
            component_attribute_class=ComponentAttributeClassGt_Maker.dc_to_tuple(
                dc.component_attribute_class
            ),
            display_name=dc.display_name,
            hw_uid=dc.hw_uid,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> Component:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: Component) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> Component:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
