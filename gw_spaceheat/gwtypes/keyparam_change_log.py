"""Type keyparam.change.log, version 000"""
import json
import logging
from typing import Any, Dict, Literal

from gridworks.errors import SchemaError
from pydantic import BaseModel, Extra, Field, validator

# enums
from enums import KindOfParam

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class KeyparamChangeLog(BaseModel):
    """
    Key Param Change Record.

    The keyparam.change.record type is designed for straightforward logging of important parameter
    changes in the SCADA and AtomicTNode code for transactive space-heating systems. Check out
    the details in [gridworks-atn]( https://github.com/thegridelectric/gridworks-atn) and [gw-scada-spaceheat-python](https://github.com/thegridelectric/gw-scada-spaceheat-python).
    It's made for humans—developers and system maintainers—to easily create and reference records
    of significant changes. Keep it short and sweet. We suggest using a "Before" and "After"
    attribute pattern to include the changed value, focusing for example on specific components
    rather than the entire hardware layout.
    """

    AboutNodeAlias: str = Field(
        title="AboutNodeAlias",
        description=(
            "The GNode (for example, the SCADA or the AtomicTNode) whose parameter is getting "
            "changed."
        ),
    )
    ChangeTimeUtc: str = Field(
        title="Change Time Utc",
        description=(
            "The time of the change. Err on the side of making sure the original parameter was "
            "used by the code at all times prior to this time. Do not be off by more than 5 minutes."
        ),
    )
    Author: str = Field(
        title="Author",
        description="The person making the change.",
    )
    ParamName: str = Field(
        title="ParamName",
        description=(
            "This may not be unique or even particularly well-defined on its own. But this can "
            "set the context for the recommended 'Before' and 'After' fields associated to this "
            "type."
        ),
    )
    Description: str = Field(
        title="Description",
        description=(
            "Clear concise description of the change. Consider including why it is a key parameter."
        ),
    )
    Kind: KindOfParam = Field(
        title="Kind of Param",
        description=(
            "This should provide a developer with the information they need to locate the parameter "
            "and its use within the relevant code base."
        ),
    )
    TypeName: Literal["keyparam.change.log"] = "keyparam.change.log"
    Version: Literal["000"] = "000"

    class Config:
        extra = Extra.allow

    @validator("AboutNodeAlias")
    def _check_about_node_alias(cls, v: str) -> str:
        try:
            check_is_left_right_dot(v)
        except ValueError as e:
            raise ValueError(
                f"AboutNodeAlias failed LeftRightDot format validation: {e}"
            )
        return v

    @validator("ChangeTimeUtc")
    def _check_change_time_utc(cls, v: str) -> str:
        try:
            check_is_log_style_date_with_millis(v)
        except ValueError as e:
            raise ValueError(
                f"ChangeTimeUtc failed LogStyleDateWithMillis format validation: {e}"
            )
        return v

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        keyparam.change.log.000 object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        keyparam.change.log.000 type. Unlike the standard python dict method,
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
        del d["Kind"]
        d["KindGtEnumSymbol"] = KindOfParam.value_to_symbol(self.Kind)
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the keyparam.change.log.000 representation.

        Instances in the class are python-native representations of keyparam.change.log.000
        objects, while the actual keyparam.change.log.000 object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is KeyparamChangeLog.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class KeyparamChangeLog_Maker:
    type_name = "keyparam.change.log"
    version = "000"

    def __init__(
        self,
        about_node_alias: str,
        change_time_utc: str,
        author: str,
        param_name: str,
        description: str,
        kind: KindOfParam,
    ):
        self.tuple = KeyparamChangeLog(
            AboutNodeAlias=about_node_alias,
            ChangeTimeUtc=change_time_utc,
            Author=author,
            ParamName=param_name,
            Description=description,
            Kind=kind,
        )

    @classmethod
    def tuple_to_type(cls, tuple: KeyparamChangeLog) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> KeyparamChangeLog:
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
    def dict_to_tuple(cls, d: dict[str, Any]) -> KeyparamChangeLog:
        """
        Deserialize a dictionary representation of a keyparam.change.log.000 message object
        into a KeyparamChangeLog python object for internal use.

        This is the near-inverse of the KeyparamChangeLog.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a SchemaError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           SchemaError: if the dict cannot be turned into a KeyparamChangeLog object.

        Returns:
            KeyparamChangeLog
        """
        d2 = dict(d)
        if "AboutNodeAlias" not in d2.keys():
            raise SchemaError(f"dict missing AboutNodeAlias: <{d2}>")
        if "ChangeTimeUtc" not in d2.keys():
            raise SchemaError(f"dict missing ChangeTimeUtc: <{d2}>")
        if "Author" not in d2.keys():
            raise SchemaError(f"dict missing Author: <{d2}>")
        if "ParamName" not in d2.keys():
            raise SchemaError(f"dict missing ParamName: <{d2}>")
        if "Description" not in d2.keys():
            raise SchemaError(f"dict missing Description: <{d2}>")
        if "KindGtEnumSymbol" not in d2.keys():
            raise SchemaError(f"KindGtEnumSymbol missing from dict <{d2}>")
        value = KindOfParam.symbol_to_value(d2["KindGtEnumSymbol"])
        d2["Kind"] = KindOfParam(value)
        del d2["KindGtEnumSymbol"]
        if "TypeName" not in d2.keys():
            raise SchemaError(f"TypeName missing from dict <{d2}>")
        if "Version" not in d2.keys():
            raise SchemaError(f"Version missing from dict <{d2}>")
        if d2["Version"] != "000":
            LOGGER.debug(
                f"Attempting to interpret keyparam.change.log version {d2['Version']} as version 000"
            )
            d2["Version"] = "000"
        return KeyparamChangeLog(**d2)


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    from typing import List

    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate <{v}> into words with split'.'")
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of <{v}> must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of <{v}> split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of <{v}> must be lowercase.")


def check_is_log_style_date_with_millis(v: str) -> None:
    """Checks LogStyleDateWithMillis format

    LogStyleDateWithMillis format:  YYYY-MM-DDTHH:mm:ss.SSS

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LogStyleDateWithMillis format. 
        In particular the milliseconds must have exactly 3 digits.
    """
    from datetime import datetime
    try:
        datetime.fromisoformat(v)
    except ValueError:
        raise ValueError(f"{v} is not in LogStyleDateWithMillis format")
    # The python fromisoformat allows for either 3 digits (milli) or 6 (micro)
    # after the final period. Make sure its 3
    milliseconds_part = v.split(".")[1]
    if len(milliseconds_part) != 3:
        raise ValueError(f"{v} is not in LogStyleDateWithMillis format."
                            " Milliseconds must have exactly 3 digits")    
    
