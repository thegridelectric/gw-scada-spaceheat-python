from typing import Dict
from schema.errors import MpSchemaError
from schema.enums.actor_class.sh_actor_class_100 import (
    ActorClass,
    ShActorClass100GtEnum,
)


class ActorClassGtEnum(ShActorClass100GtEnum):
    @classmethod
    def is_symbol(cls, candidate) -> bool:
        if candidate in cls.symbols:
            return True
        return False


class ActorClassMap:
    @classmethod
    def gt_to_local(cls, symbol):
        if not ActorClassGtEnum.is_symbol(symbol):
            raise MpSchemaError(
                f"{symbol} must belong to key of {ActorClassMap.gt_to_local_dict}"
            )
        return cls.gt_to_local_dict[symbol]

    @classmethod
    def local_to_gt(cls, actor_class):
        if not isinstance(actor_class, ActorClass):
            raise MpSchemaError(f"{actor_class} must be of type {ActorClass}")
        return cls.local_to_gt_dict[actor_class]

    gt_to_local_dict: Dict[str, ActorClass] = {
        "6d37aa41": ActorClass.SCADA,
        "32d3d19f": ActorClass.HOME_ALONE,
        "fddd0064": ActorClass.BOOLEAN_ACTUATOR,
        "2ea112b9": ActorClass.POWER_METER,
        "b103058f": ActorClass.ATN,
        "dae4b2f0": ActorClass.SIMPLE_SENSOR,
        "99a5f20d": ActorClass.NONE,
    }

    local_to_gt_dict: Dict[ActorClass, str] = {
        ActorClass.SCADA: "6d37aa41",
        ActorClass.HOME_ALONE: "32d3d19f",
        ActorClass.BOOLEAN_ACTUATOR: "fddd0064",
        ActorClass.POWER_METER: "2ea112b9",
        ActorClass.ATN: "b103058f",
        ActorClass.SIMPLE_SENSOR: "dae4b2f0",
        ActorClass.NONE: "99a5f20d",
        #
    }
