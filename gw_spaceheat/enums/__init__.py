""" GwSchema Enums used in scada """
from enums.actor_class import ActorClass
from enums.local_comm_interface import LocalCommInterface
from enums.make_model import MakeModel
from enums.role import Role
from enums.unit import Unit
from gwproto.enums.telemetry_name import TelemetryName

__all__ = [
    "LocalCommInterface",
    "ActorClass",
    "Role",
    "MakeModel",
    "Unit",
]
