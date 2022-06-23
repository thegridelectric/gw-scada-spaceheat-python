"""Makes gt.powermeter.reporting.config.100 type"""

import json
from typing import List, Optional

from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config_maker import \
    GtEqReportingConfig, GtEqReportingConfig_Maker
from schema.gt.gt_powermeter_reporting_config.gt_powermeter_reporting_config import GtPowermeterReportingConfig
from schema.errors import MpSchemaError


class GtPowermeterReportingConfig_Maker():
    type_alias = 'gt.powermeter.reporting.config.100'

    def __init__(self,
                 reporting_period_s: int,
                 poll_period_ms: int,
                 hw_uid: Optional[str],
                 eq_reporting_config_list: List[GtEqReportingConfig]):

        tuple = GtPowermeterReportingConfig(ReportingPeriodS=reporting_period_s,
                                            PollPeriodMs=poll_period_ms,
                                            HwUid=hw_uid,
                                            EqReportingConfigList=eq_reporting_config_list,
                                            )
        tuple.check_for_errors()
        self.tuple = tuple

    @classmethod
    def tuple_to_type(cls, tuple: GtPowermeterReportingConfig) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> GtPowermeterReportingConfig:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError('Type must be string or bytes!')
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> GtPowermeterReportingConfig:
        if "ReportingPeriodS" not in d.keys():
            raise MpSchemaError(f"dict {d} missing ReportingPeriodS")
        if "PollPeriodMs" not in d.keys():
            raise MpSchemaError(f"dict {d} missing PollPeriodMs")
        if "HwUid" not in d.keys():
            d["HwUid"] = None
        if "EqReportingConfigList" not in d.keys():
            raise MpSchemaError(f"dict {d} missing EqReportingConfigList")
        eq_reporting_config_list = []
        for eq_reporting_config in d["EqReportingConfigList"]:
            eq_reporting_config_list.append(GtEqReportingConfig_Maker.dict_to_tuple(eq_reporting_config))
        d["EqReportingConfigList"] = eq_reporting_config_list

        tuple = GtPowermeterReportingConfig(ReportingPeriodS=d["ReportingPeriodS"],
                                            PollPeriodMs=d["PollPeriodMs"],
                                            HwUid=d["HwUid"],
                                            EqReportingConfigList=d["EqReportingConfigList"],
                                            )
        tuple.check_for_errors()
        return tuple
