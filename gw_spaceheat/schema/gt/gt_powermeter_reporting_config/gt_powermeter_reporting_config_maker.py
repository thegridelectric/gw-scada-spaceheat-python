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
                 electrical_quantity_reporting_config_list: List[GtEqReportingConfig]):

        tuple = GtPowermeterReportingConfig(
            ReportingPeriodS=reporting_period_s,
            PollPeriodMs=poll_period_ms,
            HwUid=hw_uid,
            ElectricalQuantityReportingConfigList=electrical_quantity_reporting_config_list,
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
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]

        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")
        if "ReportingPeriodS" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ReportingPeriodS")
        if "PollPeriodMs" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing PollPeriodMs")
        if "HwUid" not in new_d.keys():
            new_d["HwUid"] = None
        if "ElectricalQuantityReportingConfigList" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing ElectricalQuantityReportingConfigList")
        electrical_quantity_reporting_config_list = []
        for eq_reporting_config in new_d["ElectricalQuantityReportingConfigList"]:
            if not isinstance(eq_reporting_config, dict):
                raise MpSchemaError(f"elt {eq_reporting_config} of ElectricalQuantityReportingConfigList must be "
                                    "EqReportingConfig but not even a dict!")
            electrical_quantity_reporting_config_list.append(GtEqReportingConfig_Maker.dict_to_tuple(eq_reporting_config))
        new_d["ElectricalQuantityReportingConfigList"] = electrical_quantity_reporting_config_list

        tuple = GtPowermeterReportingConfig(
            TypeAlias=new_d["TypeAlias"],
            ReportingPeriodS=new_d["ReportingPeriodS"],
            PollPeriodMs=new_d["PollPeriodMs"],
            HwUid=new_d["HwUid"],
            ElectricalQuantityReportingConfigList=new_d["ElectricalQuantityReportingConfigList"],
        )
        tuple.check_for_errors()
        return tuple
