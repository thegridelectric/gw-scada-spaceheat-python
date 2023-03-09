""" GwSchema Enums used in scada """
from enums.actor_class import ActorClass, ActorClassMap
from enums.local_comm_interface import (LocalCommInterface,
                                        LocalCommInterfaceMap)
from enums.make_model import MakeModel, MakeModelMap
from enums.role import Role, RoleMap
from enums.unit import Unit, UnitMap
from gwproto.enums.telemetry_name import TelemetryName
from gwproto.enums.telemetry_name_map import TelemetryNameMap

__all__ = [
    "ActorClass",
    "LocalCommInterface",
    "MakeModel",
    "Role",
    "TelemetryName",
    "Unit",
    "ActorClassMap",
    "LocalCommInterfaceMap",
    "MakeModelMap",
    "RoleMap",
    "TelemetryNameMap",
    "UnitMap",
]
