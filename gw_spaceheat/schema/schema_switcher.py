from typing import Dict, List

from gwproto.messages import (
    GsDispatch_Maker,
    GsPwr_Maker,
    GtDispatchBoolean_Maker,
    GtDispatchBooleanLocal_Maker,
    GtDriverBooleanactuatorCmd_Maker,
    GtShBooleanactuatorCmdStatus_Maker,
    GtShCliAtnCmd_Maker,
    GtShStatus_Maker,
    GtShTelemetryFromMultipurposeSensor_Maker,
    GtTelemetry_Maker,
    HeartbeatB_Maker,
    SnapshotSpaceheat_Maker,
    TelemetrySnapshotSpaceheat_Maker,
)

TypeMakerByNameDict: Dict[str, GtTelemetry_Maker] = {}

schema_makers: List[GtTelemetry_Maker] = [
    GsDispatch_Maker,
    GsPwr_Maker,
    GtDispatchBoolean_Maker,
    GtDispatchBooleanLocal_Maker,
    GtDriverBooleanactuatorCmd_Maker,
    GtShBooleanactuatorCmdStatus_Maker,
    GtShCliAtnCmd_Maker,
    GtShStatus_Maker,
    GtShTelemetryFromMultipurposeSensor_Maker,
    GtTelemetry_Maker,
    HeartbeatB_Maker,
    SnapshotSpaceheat_Maker,
    TelemetrySnapshotSpaceheat_Maker,
]

for maker in schema_makers:
    TypeMakerByNameDict[maker.type_name] = maker
