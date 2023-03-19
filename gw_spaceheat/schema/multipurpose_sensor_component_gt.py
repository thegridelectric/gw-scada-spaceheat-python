"""Type multipurpose.sensor.component.gt, version 000"""
import json
from typing import Any, Dict, List, Literal, Optional

from data_classes.components.multipurpose_sensor_component import \
    MultipurposeSensorComponent
from enums import TelemetryName
from gwproto.errors import MpSchemaError
from pydantic import BaseModel, Field, validator
from schema.telemetry_reporting_config import (TelemetryReportingConfig,
                                               TelemetryReportingConfig_Maker)


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


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods,
    most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    from typing import List

    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate {v} into words with split'.'")
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(f"Most significant word of {v} must start with alphabet char.")
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of {v} split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of {v} must be lowercase.")


class MultipurposeSensorComponentGt(BaseModel):
    """Type for tracking Multupurpose Sensor Components.

    GridWorks Spaceheat SCADA uses the GridWorks GNodeRegistry structures and
    abstractions for managing relational device data. The Component associated to
    a SpaceheatNode is part of this structure.
    [More info](https://g-node-registry.readthedocs.io/en/latest/component.html).
    """

    ComponentId: str = Field(
        title="ComponentId",
    )
    ComponentAttributeClassId: str = Field(
        title="ComponentAttributeClassId",
    )
    ChannelList: List[int] = Field(
        title="ChannelList",
    )
    ConfigList: List[TelemetryReportingConfig] = Field(
        title="ConfigList",
    )
    HwUid: Optional[str] = Field(
        title="HwUid",
        default=None,
    )
    DisplayName: Optional[str] = Field(
        title="DisplayName",
        default=None,
    )
    TypeName: Literal[
        "multipurpose.sensor.component.gt"
    ] = "multipurpose.sensor.component.gt"
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

    @validator("ConfigList")
    def _check_config_list(cls, v: List) -> List:
        for elt in v:
            if not isinstance(elt, TelemetryReportingConfig):
                raise ValueError(
                    f"elt {elt} of ConfigList must have type TelemetryReportingConfig."
                )
        return v

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()

        # Recursively call as_dict() for the SubTypes
        config_list = []
        for elt in self.ConfigList:
            config_list.append(elt.as_dict())
        d["ConfigList"] = config_list
        if d["HwUid"] is None:
            del d["HwUid"]
        if d["DisplayName"] is None:
            del d["DisplayName"]
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values())) # noqa


class MultipurposeSensorComponentGt_Maker:
    type_name = "multipurpose.sensor.component.gt"
    version = "000"

    def __init__(
        self,
        component_id: str,
        component_attribute_class_id: str,
        channel_list: List[int],
        config_list: List[TelemetryReportingConfig],
        hw_uid: Optional[str],
        display_name: Optional[str],
    ):

        self.tuple = MultipurposeSensorComponentGt(
            ComponentId=component_id,
            ComponentAttributeClassId=component_attribute_class_id,
            ChannelList=channel_list,
            ConfigList=config_list,
            HwUid=hw_uid,
            DisplayName=display_name,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: MultipurposeSensorComponentGt) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> MultipurposeSensorComponentGt:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> MultipurposeSensorComponentGt:
        d2 = dict(d)
        if "ComponentId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentId")
        if "ComponentAttributeClassId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ComponentAttributeClassId")
        if "ChannelList" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ChannelList")
        if "ConfigList" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing ConfigList")
        config_list = []
        if not isinstance(d2["ConfigList"], List):
            raise MpSchemaError("ConfigList must be a List!")
        for elt in d2["ConfigList"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of ConfigList must be "
                    "TelemetryReportingConfig but not even a dict!"
                )
            config_list.append(TelemetryReportingConfig_Maker.dict_to_tuple(elt))
        d2["ConfigList"] = config_list
        if "HwUid" not in d2.keys():
            d2["HwUid"] = None
        if "DisplayName" not in d2.keys():
            d2["DisplayName"] = None
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return MultipurposeSensorComponentGt(
            ComponentId=d2["ComponentId"],
            ComponentAttributeClassId=d2["ComponentAttributeClassId"],
            ChannelList=d2["ChannelList"],
            ConfigList=d2["ConfigList"],
            HwUid=d2["HwUid"],
            DisplayName=d2["DisplayName"],
            TypeName=d2["TypeName"],
            Version="000",
        )

    @classmethod
    def tuple_to_dc(
        cls, t: MultipurposeSensorComponentGt
    ) -> MultipurposeSensorComponent:
        if t.ComponentId in MultipurposeSensorComponent.by_id.keys():
            dc = MultipurposeSensorComponent.by_id[t.ComponentId]
        else:
            dc = MultipurposeSensorComponent(
                component_id=t.ComponentId,
                component_attribute_class_id=t.ComponentAttributeClassId,
                channel_list=t.ChannelList,
                config_list=t.ConfigList,
                hw_uid=t.HwUid,
                display_name=t.DisplayName,
            )

        return dc

    @classmethod
    def dc_to_tuple(
        cls, dc: MultipurposeSensorComponent
    ) -> MultipurposeSensorComponentGt:
        t = MultipurposeSensorComponentGt_Maker(
            component_id=dc.component_id,
            component_attribute_class_id=dc.component_attribute_class_id,
            channel_list=dc.channel_list,
            config_list=dc.config_list,
            hw_uid=dc.hw_uid,
            display_name=dc.display_name,
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> MultipurposeSensorComponent:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: MultipurposeSensorComponent) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> MultipurposeSensorComponent:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
