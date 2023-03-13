""" Enum with TypeName sh.actor.class, Version 000"""
from enum import auto
from typing import List

from fastapi_utils.enums import StrEnum


class ActorClass(StrEnum):
    """
    Determines the code running Spaceheat Nodes supervised by Spaceheat SCADA software
    [More Info](https://gridworks-protocol.readthedocs.io/en/latest/actor-class.html).

    Name (EnumSymbol, Version): description

      * NoActor (00000000, 000): A SpaceheatNode that does not have any code running on its behalf within the SCADA, but is instead only a reference object (for example, a tank of hot water or a resistive element) that can be discussed (for example, the power drawn by the resistive element can be measured) or evaluated (for example, a set of 5 different temperatures in different places on the tank can be used to estimate total thermal energy in the tank).
      * Scada (6d37aa41, 000): The SCADA actor is the prime piece of code running and supervising other ProActors within the SCADA code. It is also responsible for managing the state of TalkingWith the AtomicTNode, as well maintaining and reporting a boolean state variable that indicates whether it is following dispatch commands from the AtomicTNode XOR following dispatch commands from its own HomeAlone actor.
      * HomeAlone (32d3d19f, 000): HomeAlone is an abstract Spaceheat Actor responsible for dispatching the SCADA when it is not talking with the AtomicTNode.
      * BooleanActuator (fddd0064, 000): A SpaceheatNode representing an electric relay, that can be turned off (open circuit) or on (closed circuit).
      * PowerMeter (2ea112b9, 000): A SpaceheatNode representing the power meter that is used to settle financial transactions with the TerminalAsset. That is, this is the power meter whose accuracy is certified in the creation of the TerminalAsset GNode via creation of the TaDeed.. [More Info](https://gridworks.readthedocs.io/en/latest/terminal-asset.html).
      * Atn (b103058f, 000): A SpaceheatNode representing the AtomicTNode. Note that the code running the AtomicTNode is not local within the SCADA code, except for a stub used for testing purposes.. [More Info](https://gridworks.readthedocs.io/en/latest/atomic-t-node.html).
      * SimpleSensor (dae4b2f0, 000): A SpaceheatNode representing a sensor that measures a single category of quantity (for example, temperature) for a single object (for example, on a pipe).. [More Info](https://gridworks-protocol.readthedocs.io/en/latest/simple-sensor.html).
      * MultipurposeSensor (7c483ad0, 000): A sensor that either reads multiple kinds of readings from the same sensing device (for example reads current and voltage), reads multiple different objects (temperature from two different thermisters) or both.. [More Info](https://gridworks-protocol.readthedocs.io/en/latest/multipurpose-sensor.html).
      * Thermostat (4a9c1785, 000): A SpaceheatNode representing a thermostat.
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
