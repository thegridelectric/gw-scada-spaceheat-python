from enum import auto
from typing import List

from fastapi_utils.enums import StrEnum


class KindOfParam(StrEnum):
    """
    Supports tracking and updating various key parameters for Spaceheat SCADA and AtomicTNodes.
    This is meant in particular for by-hand updates meant to be made and later reviewed by humans,
    as opposed to a careful and precise database update process.

    Enum spaceheat.kind.of.param version 000 in the GridWorks Type registry.

    Used by used by multiple Application Shared Languages (ASLs), including but not limited to
    gwproto. For more information:
      - [ASLs](https://gridworks-type-registry.readthedocs.io/en/latest/)
      - [Global Authority](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatkindofparam)

    Values (with symbols in parens):
      - Other (00000000): A kind of parameter other than others articulated in the enumeration. This
        can of course change depending on the version of the enum. For version 000, it means
        any kind of parameter other than those in a .env file or in the hardware layout of a
        SCADA.
      - HardwareLayout (6dcdfed5): A key parameter embedded with the hardware layout object of a
        spaceheat SCADA. See for example https://github.com/thegridelectric/gw-scada-spaceheat-python.
      - DotEnv (21c96c05): A key parameter from the .env file of a spaceheat SCADA, or a spaceheat
        AtomicTNode.
    """

    Other = auto()
    HardwareLayout = auto()
    DotEnv = auto()

    @classmethod
    def default(cls) -> "KindOfParam":
        """
        Returns default value (in this case Other)
        """
        return cls.Other

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]

    @classmethod
    def version(cls, value: str) -> str:
        """
        Returns the version of an enum value.

        Once a value belongs to one version of the enum, it belongs
        to all future versions.

        Args:
            value (str): The candidate enum value.

        Raises:
            ValueError: If value is not one of the enum values.

        Returns:
            str: The earliest version of the enum containing value.
        """
        if not isinstance(value, str):
            raise ValueError(f"This method applies to strings, not enums")
        if value not in value_to_version.keys():
            raise ValueError(f"Unknown enum value: {value}")
        return value_to_version[value]

    @classmethod
    def enum_name(cls) -> str:
        """
        The name in the GridWorks Type Registry (spaceheat.kind.of.param)
        """
        return "spaceheat.kind.of.param"

    @classmethod
    def enum_version(cls) -> str:
        """
        The version in the GridWorks Type Registry (000)
        """
        return "000"

    @classmethod
    def symbol_to_value(cls, symbol: str) -> str:
        """
        Given the symbol sent in a serialized message, returns the encoded enum.

        Args:
            symbol (str): The candidate symbol.

        Returns:
            str: The encoded value associated to that symbol. If the symbol is not
            recognized - which could happen if the actor making the symbol is using
            a later version of this enum, returns the default value of "Other".
        """
        if symbol not in symbol_to_value.keys():
            return cls.default().value
        return symbol_to_value[symbol]

    @classmethod
    def value_to_symbol(cls, value: str) -> str:
        """
        Provides the encoding symbol for a KindOfParam enum to send in seriliazed messages.

        Args:
            symbol (str): The candidate value.

        Returns:
            str: The symbol encoding that value. If the value is not recognized -
            which could happen if the actor making the message used a later version
            of this enum than the actor decoding the message, returns the default
            symbol of "00000000".
        """
        if value not in value_to_symbol.keys():
            return value_to_symbol[cls.default().value]
        return value_to_symbol[value]

    @classmethod
    def symbols(cls) -> List[str]:
        """
        Returns a list of the enum symbols
        """
        return [
            "00000000",
            "6dcdfed5",
            "21c96c05",
        ]


symbol_to_value = {
    "00000000": "Other",
    "6dcdfed5": "HardwareLayout",
    "21c96c05": "DotEnv",
}

value_to_symbol = {value: key for key, value in symbol_to_value.items()}

value_to_version = {
    "Other": "000",
    "HardwareLayout": "000",
    "DotEnv": "000",
}
