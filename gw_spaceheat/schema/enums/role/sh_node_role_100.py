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
    PRIMARY_SCADA = "PrimaryScada"
    ACTUATOR = "Actuator"
    DEDICATED_THERMAL_STORE = "DedicatedThermalStore"
    HYDRONIC_PIPE = "HydronicPipe"
    SENSOR = "Sensor"
    CIRCULATOR_PUMP = "CirculatorPump"
    

class ShNodeRole100GtEnum(ABC):
    symbols: List[str] = ["f652d87f",
                          "6eb05344",
                          "eb1eb8b3",
                          "f6a567c9",
                          "cfab7629",
                          "e7a8d05a",
                          "9f13e13e",
                          "0ed56a13",
                          "d9d8f7e1",
                          "aec254fd",
                          "5247fc8e",
                          ]
