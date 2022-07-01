"""sh.actor.class.100 definition"""
import enum
from abc import ABC
from typing import List


class ActorClass(enum.Enum):
    @classmethod
    def values(cls):
        return [elt.value for elt in cls]

    SCADA = "Scada"
    HOME_ALONE = "HomeAlone"
    BOOLEAN_ACTUATOR = "BooleanActuator"
    POWER_METER = "PowerMeter"
    ATN = "Atn"
    SIMPLE_SENSOR = "SimpleSensor"
    NONE = "None"
    #


class ShActorClass100GtEnum(ABC):
    symbols: List[str] = [
        "6d37aa41",
        "32d3d19f",
        "fddd0064",
        "2ea112b9",
        "b103058f",
        "dae4b2f0",
        "99a5f20d",
        #
    ]
