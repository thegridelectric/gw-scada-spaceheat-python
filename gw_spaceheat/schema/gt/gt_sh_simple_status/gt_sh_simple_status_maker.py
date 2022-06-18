"""Makes gt.sh.simple.status.100 type"""

import json
from typing import List
from schema.gt.gt_sh_simple_status.gt_sh_simple_status import GtShSimpleStatus

from schema.errors import MpSchemaError

from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status_maker \
    import GtShSimpleSingleStatus, GtShSimpleSingleStatus_Maker


class GtShSimpleStatus_Maker():
    type_alias = 'gt.sh.simple.status.100'

    def __init__(self,
                 about_g_node_alias: str,
                 slot_start_unix_s: int,
                 reporting_period_s: int,
                 simple_single_status_list: List[GtShSimpleSingleStatus]):

        tuple = GtShSimpleStatus(AboutGNodeAlias=about_g_node_alias,
                                 SlotStartUnixS=slot_start_unix_s,
                                 ReportingPeriodS=reporting_period_s,
                                 SimpleSingleStatusList=simple_single_status_list,
                                 )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtShSimpleStatus) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtShSimpleStatus:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtShSimpleStatus:
        if "AboutGNodeAlias" not in d.keys():
            raise MpSchemaError(f"dict {d} missing AboutGNodeAlias")
        if "SlotStartUnixS" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SlotStartUnixS")
        if "ReportingPeriodS" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ReportingPeriodS")
        if "SimpleSingleStatusList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing SimpleSingleStatusList")
        if not isinstance(d["SimpleSingleStatusList"], list):
            raise MpSchemaError(f"d['SimpleSingleStatusList'] {d['SimpleSingleStatusList']} must be a list!")
        sh_simple_single_status_list = []
        for simple_single_status in d["SimpleSingleStatusList"]:
            sh_simple_single_status_list.append(GtShSimpleSingleStatus_Maker.dict_to_tuple(simple_single_status))
        d["SimpleSingleStatusList"] = sh_simple_single_status_list

        tuple = GtShSimpleStatus(AboutGNodeAlias=d["AboutGNodeAlias"],
                                 SlotStartUnixS=d["SlotStartUnixS"],
                                 ReportingPeriodS=d["ReportingPeriodS"],
                                 SimpleSingleStatusList=d["SimpleSingleStatusList"],
                                 )
        tuple.check_for_errors()
        return tuple