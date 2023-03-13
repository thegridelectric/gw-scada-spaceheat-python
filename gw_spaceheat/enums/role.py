""" Enum with TypeName sh.node.role, Version 000"""
from enum import auto
from typing import List

from fastapi_utils.enums import StrEnum


class Role(StrEnum):
    """
    Categorizes SpaceheatNodes by their function within the heating system
    [More Info](https://gridworks-protocol.readthedocs.io/en/latest/spaceheat-node-role.html).

    Name (EnumSymbol, Version): description

      * Unknown (00000000, 000): Unknown Role
      * Scada (d0afb424, 000): Primary SCADA
      * HomeAlone (863e50d1, 000): HomeAlone GNode
      * Atn (6ddff83b, 000): AtomicTNode
      * PowerMeter (9ac68b6e, 000): A SpaceheatNode representing the power meter that is used to settle financial transactions with the TerminalAsset. That is, this is the power meter whose accuracy is certified in the creation of the TerminalAsset GNode via creation of the TaDeed.. [More Info](https://gridworks.readthedocs.io/en/latest/terminal-asset.html).
      * BoostElement (99c5f326, 000): Resistive element used for providing heat to a thermal store.
      * BooleanActuator (57b788ee, 000): A solid state or mechanical relay with two states (open, closed)
      * DedicatedThermalStore (3ecfe9b8, 000): A dedicated thermal store within a thermal storage heating system - could be one or more water tanks, phase change material, etc.
      * TankWaterTempSensor (73308a1f, 000): A temperature sensor used for measuring temperature inside or on the immediate outside of a water tank.
      * PipeTempSensor (c480f612, 000): A temperature sensor used for measuring the temperature of a tank. Typically curved metal thermistor with thermal grease for good contact.
      * RoomTempSensor (fec74958, 000): A temperature sensor used for measuring room temperature, or temp in a heated space more generally.
      * OutdoorTempSensor (5938bf1f, 000): A temperature sensor used for measuring outdoor temperature.
      * PipeFlowMeter (ece3b600, 000): A meter that measures flow of liquid through a pipe, in units of VOLUME/TIME
      * HeatedSpace (65725f44, 000): A Heated Space.
      * HydronicPipe (fe3cbdd5, 000): A pipe carrying techinical water or other fluid (e.g. glycol) in a heating system.
      * BaseboardRadiator (05fdd645, 000): A baseboard radiator - one kind of emitter in a hydronic heating system.
      * RadiatorFan (6896109b, 000): A fan that can amplify the power out of a radiator.
      * CirculatorPump (b0eaf2ba, 000): Circulator pump for one or more of the hydronic pipe loops
      * MultiChannelAnalogTempSensor (661d7e73, 000): An analog multi channel temperature sensor
      * Outdoors (dd975b31, 000): The outdoors
    """

    Unknown = auto()
    Scada = auto()
    HomeAlone = auto()
    Atn = auto()
    PowerMeter = auto()
    BoostElement = auto()
    BooleanActuator = auto()
    DedicatedThermalStore = auto()
    TankWaterTempSensor = auto()
    PipeTempSensor = auto()
    RoomTempSensor = auto()
    OutdoorTempSensor = auto()
    PipeFlowMeter = auto()
    HeatedSpace = auto()
    HydronicPipe = auto()
    BaseboardRadiator = auto()
    RadiatorFan = auto()
    CirculatorPump = auto()
    MultiChannelAnalogTempSensor = auto()
    Outdoors = auto()

    @classmethod
    def default(cls) -> "Role":
        """
        Returns default value Unknown
        """
        return cls.Unknown

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns enum choices
        """
        return [elt.value for elt in cls]
