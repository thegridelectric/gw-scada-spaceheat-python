from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.role.sh_node_role_110 import (
    Role,
    ShNodeRole110GtEnum,
)


class RoleGtEnum(ShNodeRole110GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class RoleMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not RoleGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {RoleMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, role):
        if not isinstance(role, Role):
            raise MpSchemaError(f"{role} must be of type {Role}")
        return cls.local_to_gt_dict[role]

    gt_to_local_dict: Dict[str, Role] = {
        "99c5f326": Role.BOOST_ELEMENT,
        "ece3b600": Role.PIPE_FLOW_METER,
        "9ac68b6e": Role.POWER_METER,
        "65725f44": Role.HEATED_SPACE,
        "d0afb424": Role.SCADA,
        "fe3cbdd5": Role.HYDRONIC_PIPE,
        "c480f612": Role.PIPE_TEMP_SENSOR,
        "05fdd645": Role.BASEBOARD_RADIATOR,
        "6896109b": Role.RADIATOR_FAN,
        "b0eaf2ba": Role.CIRCULATOR_PUMP,
        "73308a1f": Role.TANK_WATER_TEMP_SENSOR,
        "fec74958": Role.ROOM_TEMP_SENSOR,
        "3ecfe9b8": Role.DEDICATED_THERMAL_STORE,
        "5938bf1f": Role.OUTDOOR_TEMP_SENSOR,
        "57b788ee": Role.BOOLEAN_ACTUATOR,
        "6ddff83b": Role.ATN,
        "863e50d1": Role.HOME_ALONE,
        "dd975b31": Role.OUTDOORS,
    }

    local_to_gt_dict: Dict[Role, str] = {
        Role.BOOST_ELEMENT: "99c5f326",
        Role.PIPE_FLOW_METER: "ece3b600",
        Role.POWER_METER: "9ac68b6e",
        Role.HEATED_SPACE: "65725f44",
        Role.SCADA: "d0afb424",
        Role.HYDRONIC_PIPE: "fe3cbdd5",
        Role.PIPE_TEMP_SENSOR: "c480f612",
        Role.BASEBOARD_RADIATOR: "05fdd645",
        Role.RADIATOR_FAN: "6896109b",
        Role.CIRCULATOR_PUMP: "b0eaf2ba",
        Role.TANK_WATER_TEMP_SENSOR: "73308a1f",
        Role.ROOM_TEMP_SENSOR: "fec74958",
        Role.DEDICATED_THERMAL_STORE: "3ecfe9b8",
        Role.OUTDOOR_TEMP_SENSOR: "5938bf1f",
        Role.BOOLEAN_ACTUATOR: "57b788ee",
        Role.ATN: "6ddff83b",
        Role.HOME_ALONE: "863e50d1",
        Role.OUTDOORS: "dd975b31",
        #
    }
