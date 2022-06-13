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
        "f652d87f": Role.HEATED_SPACE,
        "6eb05344": Role.OUTDOORS,
        "eb1eb8b3": Role.ELECTRIC_HEATER,
        "f6a567c9": Role.POWER_METER,
        "cfab7629": Role.ATOMIC_T_NODE,
        "64044e41": Role.BASEBOARD_RADIATOR,
        "e7a8d05a": Role.PRIMARY_SCADA,
        "9f13e13e": Role.ACTUATOR,
        "0ed56a13": Role.DEDICATED_THERMAL_STORE,
        "d9d8f7e1": Role.HYDRONIC_PIPE,
        "aec254fd": Role.SENSOR,
        "5247fc8e": Role.CIRCULATOR_PUMP, }

    local_to_gt_dict: Dict[Role, str] = {
        Role.HEATED_SPACE: "f652d87f",
        Role.OUTDOORS: "6eb05344",
        Role.ELECTRIC_HEATER: "eb1eb8b3",
        Role.POWER_METER: "f6a567c9",
        Role.ATOMIC_T_NODE: "cfab7629",
        Role.BASEBOARD_RADIATOR: "64044e41",
        Role.PRIMARY_SCADA: "e7a8d05a",
        Role.ACTUATOR: "9f13e13e",
        Role.DEDICATED_THERMAL_STORE: "0ed56a13",
        Role.HYDRONIC_PIPE: "d9d8f7e1",
        Role.SENSOR: "aec254fd",
        Role.CIRCULATOR_PUMP: "5247fc8e",
         }
