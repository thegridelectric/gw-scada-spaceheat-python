"""sh.node.role.100 definition"""
from abc import ABC
import enum
from typing import List


class Role(enum.Enum):
    HEATED_SPACE = "HeatedSpace"
    OUTDOORS = "Outdoors"
    ELECTRIC_HEATER = "ElectricHeater"
    POWER_METER = "PowerMeter"
    ATOMIC_T_NODE = "AtomicTNode"
    BASEBOARD_RADIATOR = "BaseboardRadiator"
    PRIMARY_SCADA = "PrimaryScada"
    ACTUATOR = "Actuator"
    DEDICATED_THERMAL_STORE = "DedicatedThermalStore"
    HYDRONIC_PIPE = "HydronicPipe"
    SENSOR = "Sensor"
    CIRCULATOR_PUMP = "CirculatorPump"
    

class ShNodeRole100GtEnum(ABC):
    symbols: List[str] = ["65725f44",
                          "dd975b31",
                          "99c5f326",
                          "9ac68b6e",
                          "6ddff83b",
                          "05fdd645",
                          "d0afb424",
                          "57b788ee",
                          "3ecfe9b8",
                          "fe3cbdd5",
                          "aec254fd",
                          "b0eaf2ba",
                          ]
