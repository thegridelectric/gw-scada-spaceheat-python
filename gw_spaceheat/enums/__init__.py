"""
GridWorks Type Registry Enums used in Spaceheat SCADA code
"""

# Enums from gwproto
from gwproto.enums.actor_class import ActorClass
from gwproto.enums.make_model import MakeModel
from gwproto.enums.telemetry_name import TelemetryName
from gwproto.enums.unit import Unit

# Enums from scada
from enums.kind_of_param import KindOfParam


__all__ = [
    "ActorClass",  # [sh.actor.class version 001](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shactorclass)
    "MakeModel",  # [spaceheat.make.model version 001](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatmakemodel)
    "TelemetryName",  # [spaceheat.telemetry.name version 001](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheattelemetryname)
    "Unit",  # [spaceheat.unit version 000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatunit)
    "KindOfParam",  # [spaceheat.kind.of.param.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatkindofparam)
]
