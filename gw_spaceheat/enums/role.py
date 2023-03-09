from abc import ABC
from enum import auto
from typing import Dict, List

from fastapi_utils.enums import StrEnum
from gwproto.errors import MpSchemaError


class Role(StrEnum):
    """
    Categorizes SpaceheatNodes by their function within the heating system.
    [More Info](https://gridworks-protocol.readthedocs.io/en/latest/spaceheat-node-role.html).

    Choices and descriptions:

      * Unknown: Unknown Role
      * Scada: Primary SCADA
      * HomeAlone: HomeAlone GNode
      * Atn: AtomicTNode
      * PowerMeter: A SpaceheatNode representing the power meter that is used to settle financial transactions with the TerminalAsset. That is, this is the power meter whose accuracy is certified in the creation of the TerminalAsset GNode via creation of the TaDeed.. [More Info](https://gridworks.readthedocs.io/en/latest/terminal-asset.html).
      * BoostElement: Resistive element used for providing heat to a thermal store.
      * BooleanActuator: A solid state or mechanical relay with two states (open, closed)
      * DedicatedThermalStore: A dedicated thermal store within a thermal storage heating system - could be one or more water tanks, phase change material, etc.
      * TankWaterTempSensor: A temperature sensor used for measuring temperature inside or on the immediate outside of a water tank.
      * PipeTempSensor: A temperature sensor used for measuring the temperature of a tank. Typically curved metal thermistor with thermal grease for good contact.
      * RoomTempSensor: A temperature sensor used for measuring room temperature, or temp in a heated space more generally.
      * OutdoorTempSensor: A temperature sensor used for measuring outdoor temperature.
      * PipeFlowMeter: A meter that measures flow of liquid through a pipe, in units of VOLUME/TIME
      * HeatedSpace: A Heated Space.
      * HydronicPipe: A pipe carrying techinical water or other fluid (e.g. glycol) in a heating system.
      * BaseboardRadiator: A baseboard radiator - one kind of emitter in a hydronic heating system.
      * RadiatorFan: A fan that can amplify the power out of a radiator.
      * CirculatorPump: Circulator pump for one or more of the hydronic pipe loops
      * MultiChannelAnalogTempSensor: An analog multi channel temperature sensor
      * Outdoors: The outdoors
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


class ShNodeRole110GtEnum(ABC):
    symbols: List[str] = [
        "00000000",
        "d0afb424",
        "863e50d1",
        "6ddff83b",
        "9ac68b6e",
        "99c5f326",
        "57b788ee",
        "3ecfe9b8",
        "73308a1f",
        "c480f612",
        "fec74958",
        "5938bf1f",
        "ece3b600",
        "65725f44",
        "fe3cbdd5",
        "05fdd645",
        "6896109b",
        "b0eaf2ba",
        "661d7e73",
        "dd975b31",
        #
    ]


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
        "00000000": Role.Unknown,
        "d0afb424": Role.Scada,
        "863e50d1": Role.HomeAlone,
        "6ddff83b": Role.Atn,
        "9ac68b6e": Role.PowerMeter,
        "99c5f326": Role.BoostElement,
        "57b788ee": Role.BooleanActuator,
        "3ecfe9b8": Role.DedicatedThermalStore,
        "73308a1f": Role.TankWaterTempSensor,
        "c480f612": Role.PipeTempSensor,
        "fec74958": Role.RoomTempSensor,
        "5938bf1f": Role.OutdoorTempSensor,
        "ece3b600": Role.PipeFlowMeter,
        "65725f44": Role.HeatedSpace,
        "fe3cbdd5": Role.HydronicPipe,
        "05fdd645": Role.BaseboardRadiator,
        "6896109b": Role.RadiatorFan,
        "b0eaf2ba": Role.CirculatorPump,
        "661d7e73": Role.MultiChannelAnalogTempSensor,
        "dd975b31": Role.Outdoors,
    }

    local_to_gt_dict: Dict[Role, str] = {
        Role.Unknown: "00000000",
        Role.Scada: "d0afb424",
        Role.HomeAlone: "863e50d1",
        Role.Atn: "6ddff83b",
        Role.PowerMeter: "9ac68b6e",
        Role.BoostElement: "99c5f326",
        Role.BooleanActuator: "57b788ee",
        Role.DedicatedThermalStore: "3ecfe9b8",
        Role.TankWaterTempSensor: "73308a1f",
        Role.PipeTempSensor: "c480f612",
        Role.RoomTempSensor: "fec74958",
        Role.OutdoorTempSensor: "5938bf1f",
        Role.PipeFlowMeter: "ece3b600",
        Role.HeatedSpace: "65725f44",
        Role.HydronicPipe: "fe3cbdd5",
        Role.BaseboardRadiator: "05fdd645",
        Role.RadiatorFan: "6896109b",
        Role.CirculatorPump: "b0eaf2ba",
        Role.MultiChannelAnalogTempSensor: "661d7e73",
        Role.Outdoors: "dd975b31",
        #
    }
