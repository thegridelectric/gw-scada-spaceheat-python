from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.units.spaceheat_units_100 import Units, SpaceheatUnits100GtEnum


class UnitsGtEnum(SpaceheatUnits100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class UnitsMap():
    @classmethod
    def gt_to_local(cls, symbol):
        if not UnitsGtEnum.is_symbol(symbol):
            raise MpSchemaError(f"{symbol} must belong to key of {UnitsMap.gt_to_local_dict}")
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, units):
        if not isinstance(units, Units):
            raise MpSchemaError(f"{units} must be of type {Units}")
        return cls.local_to_gt_dict[units]

    gt_to_local_dict: Dict[str, Units] = {
        "ec14bd47": Units.CELCIUS,
        "7d8832f8": Units.FAHRENHEIT,
        "f459a9c3": Units.W,
        "ec972387": Units.UNITLESS, }

    local_to_gt_dict: Dict[Units, str] = {
        Units.CELCIUS: "ec14bd47",
        Units.FAHRENHEIT: "7d8832f8",
        Units.W: "f459a9c3",
        Units.UNITLESS: "ec972387",
         }
