from typing import Dict, List

from schema.gs.gs_dispatch_maker import GsDispatch_Maker
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.gt.gt_dispatch.gt_dispatch_maker import GtDispatch_Maker
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd_maker \
    import GtDriverBooleanactuatorCmd_Maker
from schema.gt.gt_sh_cli_atn_cmd.gt_sh_cli_atn_cmd_maker import GtShCliAtnCmd_Maker
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response_maker import (
    GtShCliScadaResponse_Maker,
)

from schema.gt.gt_sh_status.gt_sh_status_maker import (
    GtShStatus_Maker,
)
from schema.gt.gt_sh_status_snapshot.gt_sh_status_snapshot_maker import GtShStatusSnapshot_Maker
from schema.gt.gt_sh_telemetry_from_multipurpose_sensor.gt_sh_telemetry_from_multipurpose_sensor_maker import (
    GtShTelemetryFromMultipurposeSensor_Maker,
)
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker

TypeMakerByAliasDict: Dict[str, GtTelemetry_Maker] = {}
schema_makers: List[GtTelemetry_Maker] = [
    GsDispatch_Maker,
    GsPwr_Maker,
    GtDispatch_Maker,
    GtDriverBooleanactuatorCmd_Maker,
    GtShCliAtnCmd_Maker,
    GtShCliScadaResponse_Maker,
    GtShStatus_Maker,
    GtShStatusSnapshot_Maker,
    GtShTelemetryFromMultipurposeSensor_Maker,
    GtTelemetry_Maker,
]

for maker in schema_makers:
    TypeMakerByAliasDict[maker.type_alias] = maker
