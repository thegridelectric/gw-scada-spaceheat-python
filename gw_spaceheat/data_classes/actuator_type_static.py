from typing import Dict
from .actuator_type import ActuatorType

PlatformActuatorType: Dict[str,ActuatorType] = {}

""" ELECTRIC_RELAY """
ELECTRIC_RELAY= ActuatorType(value = "ElectricRelay",
            display_name = "Electric Relay")

PlatformActuatorType[ELECTRIC_RELAY.value] = ELECTRIC_RELAY

