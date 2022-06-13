from typing import Dict, List
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker
from schema.gs.gs_dispatch_maker import GsDispatch_Maker
from schema.gs.gs_pwr_maker import GsPwr_Maker

SchemaMakerByAliasDict: Dict[str, GtTelemetry_Maker] = {}
schema_makers: List[GtTelemetry_Maker] = [GtTelemetry_Maker, 
                 GsDispatch_Maker, 
                 GsPwr_Maker]

for maker in schema_makers:
    SchemaMakerByAliasDict[maker.type_alias] = maker