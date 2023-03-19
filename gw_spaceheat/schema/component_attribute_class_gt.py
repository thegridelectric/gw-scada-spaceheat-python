"""Type component.attribute.class.gt, version 000"""
import json
from typing import Any, Dict, Literal, Optional

from data_classes.component_attribute_class import ComponentAttributeClass
from gwproto.errors import MpSchemaError
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


class ComponentAttributeClassGt(BaseModel):
    """ """

    ComponentAttributeClassId: str = Field(
        title="ComponentAttributeClassId",
        default="29c5257b-8a86-4dbe-a9d4-9c7330c3c4d0",
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    TypeName: Literal["component.attribute.class.gt"] = "component.attribute.class.gt"
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

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        if d["DisplayName"] is None:
            del d["DisplayName"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values())) # noqa

class ComponentAttributeClassGt_Maker:
    type_name = "component.attribute.class.gt"
    version = "000"

    def __init__(self, component_attribute_class_id: str, display_name: Optional[str]):

        self.tuple = ComponentAttributeClassGt(
            ComponentAttributeClassId=component_attribute_class_id,
            DisplayName=display_name,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: ComponentAttributeClassGt) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> ComponentAttributeClassGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> ComponentAttributeClassGt:
        d2 = dict(d)
        if "ComponentAttributeClassId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return ComponentAttributeClassGt(
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            DisplayName=d2["DisplayName"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(cls, t: ComponentAttributeClassGt) -> ComponentAttributeClass:
        if t.ComponentAttributeClassId in ComponentAttributeClass.by_id.keys():
            dc = ComponentAttributeClass.by_id[t.ComponentAttributeClassId]
        else:
            dc = ComponentAttributeClass(
                component_attribute_class_id=t.ComponentAttributeClassId,
                display_name=t.DisplayName,
            )

        return dc

    @classmethod
    def dc_to_tuple(cls, dc: ComponentAttributeClass) -> ComponentAttributeClassGt:
        t = ComponentAttributeClassGt_Maker(
            component_attribute_class_id=dc.component_attribute_class_id,
            display_name=dc.display_name,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> ComponentAttributeClass:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: ComponentAttributeClass) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> ComponentAttributeClass:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
