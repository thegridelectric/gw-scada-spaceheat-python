from typing import Dict, List

from gwproto.messages import  GsDispatch_Maker
from gwproto.messages import  GsPwr_Maker
from gwproto.messages import  GtDispatchBoolean_Maker
from gwproto.messages import  GtDispatchBooleanLocal_Maker
from gwproto.messages import  GtDriverBooleanactuatorCmd_Maker
from gwproto.messages import  GtShCliAtnCmd_Maker
from gwproto.messages import  TelemetrySnapshotSpaceheat_Maker
from gwproto.messages import  GtShStatus_Maker
from gwproto.messages import  SnapshotSpaceheat_Maker
from gwproto.messages import  GtShTelemetryFromMultipurposeSensor_Maker
from gwproto.messages import  GtTelemetry_Maker

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

