from abc import ABC
from enum import auto
from typing import Dict, List

from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError


class ActorClass(StrEnum):
    """
    Determines the code running Spaceheat Nodes supervised by Spaceheat SCADA software. [More Info](https://gridworks-protocol.readthedocs.io/en/latest/actor-class.html).

    Choices and descriptions:

      * NoActor: A SpaceheatNode that does not have any code running on its behalf within the SCADA, but is instead only a reference object (for example, a tank of hot water or a resistive element) that can be discussed (for example, the power drawn by the resistive element can be measured) or evaluated (for example, a set of 5 different temperatures in different places on the tank can be used to estimate total thermal energy in the tank).
      * Scada: The SCADA actor is the prime piece of code running and supervising other ProActors within the SCADA code. It is also responsible for managing the state of TalkingWith the AtomicTNode, as well maintaining and reporting a boolean state variable that indicates whether it is following dispatch commands from the AtomicTNode XOR following dispatch commands from its own HomeAlone actor.
      * HomeAlone: HomeAlone is an abstract Spaceheat Actor responsible for dispatching the SCADA when it is not talking with the AtomicTNode.
      * BooleanActuator: A SpaceheatNode representing an electric relay, that can be turned off (open circuit) or on (closed circuit).
      * PowerMeter: A SpaceheatNode representing the power meter that is used to settle financial transactions with the TerminalAsset. That is, this is the power meter whose accuracy is certified in the creation of the TerminalAsset GNode via creation of the TaDeed.. [More Info](https://gridworks.readthedocs.io/en/latest/terminal-asset.html).
      * Atn: A SpaceheatNode representing the AtomicTNode. Note that the code running the AtomicTNode is not local within the SCADA code, except for a stub used for testing purposes.. [More Info](https://gridworks.readthedocs.io/en/latest/atomic-t-node.html).
      * SimpleSensor: A SpaceheatNode representing a sensor that measures a single category of quantity (for example, temperature) for a single object (for example, on a pipe).. [More Info](https://gridworks-protocol.readthedocs.io/en/latest/simple-sensor.html).
      * MultipurposeSensor: A sensor that either reads multiple kinds of readings from the same sensing device (for example reads current and voltage), reads multiple different objects (temperature from two different thermisters) or both.. [More Info](https://gridworks-protocol.readthedocs.io/en/latest/multipurpose-sensor.html).
      * Thermostat: A SpaceheatNode representing a thermostat.
    """

    NoActor = auto()
    Scada = auto()
    HomeAlone = auto()
    BooleanActuator = auto()
    PowerMeter = auto()
    Atn = auto()
    SimpleSensor = auto()
    MultipurposeSensor = auto()
    Thermostat = auto()

    @classmethod
    def default(cls) -> "ActorClass":
        """
        Returns default value NoActor
        """
        return cls.NoActor

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]


class ShActorClass100GtEnum(ABC):
    symbols: List[str] = [
        "00000000",
        "6d37aa41",
        "32d3d19f",
        "fddd0064",
        "2ea112b9",
        "b103058f",
        "dae4b2f0",
        "7c483ad0",
        "4a9c1785",
        #
    ]


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
        "00000000": ActorClass.NoActor,
        "6d37aa41": ActorClass.Scada,
        "32d3d19f": ActorClass.HomeAlone,
        "fddd0064": ActorClass.BooleanActuator,
        "2ea112b9": ActorClass.PowerMeter,
        "b103058f": ActorClass.Atn,
        "dae4b2f0": ActorClass.SimpleSensor,
        "7c483ad0": ActorClass.MultipurposeSensor,
        "4a9c1785": ActorClass.Thermostat,
    }

    local_to_gt_dict: Dict[ActorClass, str] = {
        ActorClass.NoActor: "00000000",
        ActorClass.Scada: "6d37aa41",
        ActorClass.HomeAlone: "32d3d19f",
        ActorClass.BooleanActuator: "fddd0064",
        ActorClass.PowerMeter: "2ea112b9",
        ActorClass.Atn: "b103058f",
        ActorClass.SimpleSensor: "dae4b2f0",
        ActorClass.MultipurposeSensor: "7c483ad0",
        ActorClass.Thermostat: "4a9c1785",
        #
    }
