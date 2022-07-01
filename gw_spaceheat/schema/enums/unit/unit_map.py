from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.unit.spaceheat_unit_100 import (
    Unit,
    SpaceheatUnit100GtEnum,
)


class UnitGtEnum(SpaceheatUnit100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class UnitMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not UnitGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {UnitMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, unit):
        if not isinstance(unit, Unit):
            raise MpSchemaError(f"{unit} must be of type {Unit}")
        return cls.local_to_gt_dict[unit]

    gt_to_local_dict: Dict[str, Unit] = {
        "ec14bd47": Unit.CELCIUS,
        "a969ac7c": Unit.AMPS_RMS,
        "b4580361": Unit.GPM,
        "7d8832f8": Unit.FAHRENHEIT,
        "f459a9c3": Unit.W,
        "ec972387": Unit.UNITLESS,
    }

    local_to_gt_dict: Dict[Unit, str] = {
        Unit.CELCIUS: "ec14bd47",
        Unit.AMPS_RMS: "a969ac7c",
        Unit.GPM: "b4580361",
        Unit.FAHRENHEIT: "7d8832f8",
        Unit.W: "f459a9c3",
        Unit.UNITLESS: "ec972387",
        #
    }
