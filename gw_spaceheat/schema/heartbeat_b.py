"""Type heartbeat.b, version 001"""
import json
from typing import Any, Dict, Literal

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


def check_is_hex_char(v: str) -> None:
    """Checks HexChar format

    HexChar format: single-char string in '0123456789abcdefABCDEF'

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not HexChar format
    """
    if not isinstance(v, str):
        raise ValueError(f"{v} must be a hex char, but not even a string")
    if len(v) > 1:
        raise ValueError(f"{v} must be a hex char, but not of len 1")
    if v not in "0123456789abcdefABCDEF":
        raise ValueError(f"{v} must be one of '0123456789abcdefABCDEF'")


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


def check_is_reasonable_unix_time_ms(v: int) -> None:
    """Checks ReasonableUnixTimeMs format

    ReasonableUnixTimeMs format: unix milliseconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeMs format
    """
    import pendulum

    if pendulum.parse("2000-01-01T00:00:00Z").int_timestamp * 1000 > v:  # type: ignore[union-attr]
        raise ValueError(f"{v} must be after Jan 1 2000")
    if pendulum.parse("3000-01-01T00:00:00Z").int_timestamp * 1000 < v:  # type: ignore[union-attr]
        raise ValueError(f"{v} must be before Jan 1 3000")


class HeartbeatB(BaseModel):
    """.

    Heartbeat for Scada-AtomicTNode DispatchContract, to send via RabbitMQ
    """

    FromGNodeAlias: str = Field(
        title="My GNodeAlias",
    )
    FromGNodeInstanceId: str = Field(
        title="My GNodeInstanceId",
    )
    MyHex: str = Field(
        title="Hex character getting sent",
        default="0",
    )
    YourLastHex: str = Field(
        title="Last hex character received from heartbeat partner.",
    )
    LastReceivedTimeUnixMs: int = Field(
        title="Time YourLastHex was received on my clock",
    )
    SendTimeUnixMs: int = Field(
        title="Time this message is made and sent on my clock",
    )
    StartingOver: bool = Field(
        title="True if the heartbeat initiator wants to start the volley over",
        description="(typically the AtomicTNode in an AtomicTNode / SCADA pair) wants "
                    "to start the heartbeating volley over. The result is that its partner "
                    "will not expect the initiator to know its last Hex.",
    )
    TypeName: Literal["heartbeat.b"] = "heartbeat.b"
    Version: str = "001"

    @validator("FromGNodeAlias")
    def _check_from_g_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"FromGNodeAlias failed LeftRightDot format validation: {e}"
            )
        return v

    @validator("FromGNodeInstanceId")
    def _check_from_g_node_instance_id(cls, v: str) -> str:
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"FromGNodeInstanceId failed UuidCanonicalTextual format validation: {e}"
            )
        return v

    @validator("MyHex")
    def _check_my_hex(cls, v: str) -> str:
        try:
            check_is_hex_char(v)
        except ValueError as e:
            raise ValueError(f"MyHex failed HexChar format validation: {e}")
        return v

    @validator("YourLastHex")
    def _check_your_last_hex(cls, v: str) -> str:
        try:
            check_is_hex_char(v)
        except ValueError as e:
            raise ValueError(f"YourLastHex failed HexChar format validation: {e}")
        return v

    @validator("LastReceivedTimeUnixMs")
    def _check_last_received_time_unix_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"LastReceivedTimeUnixMs failed ReasonableUnixTimeMs format validation: {e}"
            )
        return v

    @validator("SendTimeUnixMs")
    def _check_send_time_unix_ms(cls, v: int) -> int:
        try:
            check_is_reasonable_unix_time_ms(v)
        except ValueError as e:
            raise ValueError(
                f"SendTimeUnixMs failed ReasonableUnixTimeMs format validation: {e}"
            )
        return v

    def as_dict(self) -> Dict[str, Any]:
        d = self.dict()
        return d

    def as_type(self) -> str:
        return json.dumps(self.as_dict())


class HeartbeatB_Maker:
    type_name = "heartbeat.b"
    version = "001"

    def __init__(
        self,
        from_g_node_alias: str,
        from_g_node_instance_id: str,
        my_hex: str,
        your_last_hex: str,
        last_received_time_unix_ms: int,
        send_time_unix_ms: int,
        starting_over: bool,
    ):

        self.tuple = HeartbeatB(
            FromGNodeAlias=from_g_node_alias,
            FromGNodeInstanceId=from_g_node_instance_id,
            MyHex=my_hex,
            YourLastHex=your_last_hex,
            LastReceivedTimeUnixMs=last_received_time_unix_ms,
            SendTimeUnixMs=send_time_unix_ms,
            StartingOver=starting_over,
            #
        )

    @classmethod
    def tuple_to_type(cls, tuple: HeartbeatB) -> str:
        """
        Given a Python class object, returns the serialized JSON type object
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> HeartbeatB:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> HeartbeatB:
        d2 = dict(d)
        if "FromGNodeAlias" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing FromGNodeAlias")
        if "FromGNodeInstanceId" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing FromGNodeInstanceId")
        if "MyHex" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing MyHex")
        if "YourLastHex" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing YourLastHex")
        if "LastReceivedTimeUnixMs" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing LastReceivedTimeUnixMs")
        if "SendTimeUnixMs" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing SendTimeUnixMs")
        if "StartingOver" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing StartingOver")
        if "TypeName" not in d2.keys():
            raise MpSchemaError(f"dict {d2} missing TypeName")

        return HeartbeatB(
            FromGNodeAlias=d2["FromGNodeAlias"],
            FromGNodeInstanceId=d2["FromGNodeInstanceId"],
            MyHex=d2["MyHex"],
            YourLastHex=d2["YourLastHex"],
            LastReceivedTimeUnixMs=d2["LastReceivedTimeUnixMs"],
            SendTimeUnixMs=d2["SendTimeUnixMs"],
            StartingOver=d2["StartingOver"],
            TypeName=d2["TypeName"],
            Version="001",
        )
