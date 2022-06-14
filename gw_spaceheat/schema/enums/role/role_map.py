from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.role.sh_node_role_100 import Role, ShNodeRole100GtEnum


class RoleGtEnum(ShNodeRole100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class RoleMap():
    @classmethod
    def gt_to_local(cls, symbol):
        if not RoleGtEnum.is_symbol(symbol):
            raise MpSchemaError(f"{symbol} must belong to key of {RoleMap.gt_to_local_dict}")
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, role):
        if not isinstance(role, Role):
            raise MpSchemaError(f"{role} must be of type {Role}")
        return cls.local_to_gt_dict[role]

    gt_to_local_dict: Dict[str, Role] = {
        "65725f44": Role.HEATED_SPACE,
        "dd975b31": Role.OUTDOORS,
        "99c5f326": Role.ELECTRIC_HEATER,
        "9ac68b6e": Role.POWER_METER,
        "6ddff83b": Role.ATOMIC_T_NODE,
        "05fdd645": Role.BASEBOARD_RADIATOR,
        "d0afb424": Role.PRIMARY_SCADA,
        "57b788ee": Role.ACTUATOR,
        "3ecfe9b8": Role.DEDICATED_THERMAL_STORE,
        "fe3cbdd5": Role.HYDRONIC_PIPE,
        "aec254fd": Role.SENSOR,
        "b0eaf2ba": Role.CIRCULATOR_PUMP, }

    local_to_gt_dict: Dict[Role, str] = {
        Role.HEATED_SPACE: "65725f44",
        Role.OUTDOORS: "dd975b31",
        Role.ELECTRIC_HEATER: "99c5f326",
        Role.POWER_METER: "9ac68b6e",
        Role.ATOMIC_T_NODE: "6ddff83b",
        Role.BASEBOARD_RADIATOR: "05fdd645",
        Role.PRIMARY_SCADA: "d0afb424",
        Role.ACTUATOR: "57b788ee",
        Role.DEDICATED_THERMAL_STORE: "3ecfe9b8",
        Role.HYDRONIC_PIPE: "fe3cbdd5",
        Role.SENSOR: "aec254fd",
        Role.CIRCULATOR_PUMP: "b0eaf2ba",
         }
