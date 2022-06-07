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
        "f652d87f": Role.HEATEDSPACE,
        "6eb05344": Role.OUTDOORS,
        "eb1eb8b3": Role.ELECTRICHEATER,
        "f6a567c9": Role.POWERMETER,
        "cfab7629": Role.ATOMICTNODE,
        "e7a8d05a": Role.PRIMARYSCADA,
        "9f13e13e": Role.ACTUATOR,
        "0ed56a13": Role.DEDICATEDTHERMALSTORE,
        "d9d8f7e1": Role.HYDRONICPIPE,
        "aec254fd": Role.SENSOR,
        "5247fc8e": Role.CIRCULATORPUMP, }

    local_to_gt_dict: Dict[Role, str] = {
        Role.HEATEDSPACE: "f652d87f",
        Role.OUTDOORS: "6eb05344",
        Role.ELECTRICHEATER: "eb1eb8b3",
        Role.POWERMETER: "f6a567c9",
        Role.ATOMICTNODE: "cfab7629",
        Role.PRIMARYSCADA: "e7a8d05a",
        Role.ACTUATOR: "9f13e13e",
        Role.DEDICATEDTHERMALSTORE: "0ed56a13",
        Role.HYDRONICPIPE: "d9d8f7e1",
        Role.SENSOR: "aec254fd",
        Role.CIRCULATORPUMP: "5247fc8e",
         }
