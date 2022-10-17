from typing import Dict, List

from schema.messages import GsDispatch_Maker
from schema.messages import GsPwr_Maker
from schema.messages import GtDispatchBoolean_Maker
from schema.messages import GtDispatchBooleanLocal_Maker
from schema.messages import GtDriverBooleanactuatorCmd_Maker
from schema.messages import GtShCliAtnCmd_Maker
from schema.messages import TelemetrySnapshotSpaceheat_Maker
from schema.messages import GtShStatus_Maker
from schema.messages import SnapshotSpaceheat_Maker
from schema.messages import GtShTelemetryFromMultipurposeSensor_Maker
from schema.messages import GtTelemetry_Maker

TypeMakerByAliasDict: Dict[str, GtTelemetry_Maker] = {}
schema_makers: List[GtTelemetry_Maker] = [
    GsDispatch_Maker,
    GsPwr_Maker,
    GtDispatchBoolean_Maker,
    GtDispatchBooleanLocal_Maker,
    GtDriverBooleanactuatorCmd_Maker,
    GtShCliAtnCmd_Maker,
    TelemetrySnapshotSpaceheat_Maker,
    GtShStatus_Maker,
    SnapshotSpaceheat_Maker,
    GtShTelemetryFromMultipurposeSensor_Maker,
    GtTelemetry_Maker,
]

for maker in schema_makers:
    TypeMakerByAliasDict[maker.type_alias] = maker

