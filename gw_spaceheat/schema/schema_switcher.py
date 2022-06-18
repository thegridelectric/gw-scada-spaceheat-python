from typing import Dict, List
from schema.gt.gt_telemetry.gt_telemetry_maker import GtTelemetry_Maker
from schema.gs.gs_dispatch_maker import GsDispatch_Maker
from schema.gs.gs_pwr_maker import GsPwr_Maker
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_maker \
    import GtShSimpleStatus_Maker
from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status_maker \
    import GtShSimpleSingleStatus_Maker
from schema.gt.gt_dispatch.gt_dispatch_maker \
    import GtDispatch_Maker


TypeMakerByAliasDict: Dict[str, GtTelemetry_Maker] = {}
schema_makers: List[GtTelemetry_Maker] = [GtTelemetry_Maker,
                                          GsDispatch_Maker,
                                          GsPwr_Maker,
                                          GtShSimpleStatus_Maker,
                                          GtShSimpleSingleStatus_Maker,
                                          GtDispatch_Maker]

for maker in schema_makers:
    TypeMakerByAliasDict[maker.type_alias] = maker