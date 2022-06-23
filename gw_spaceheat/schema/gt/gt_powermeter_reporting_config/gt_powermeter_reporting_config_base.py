"""Base for gt.powermeter.reporting.config.100 """
import json
from typing import List, NamedTuple
from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config_maker import \
    GtEqReportingConfig


class GtPowermeterReportingConfigBase(NamedTuple):
    ReportingPeriodS: int     #
    PollPeriodMs: int  #
    EqReportingConfigList: List[GtEqReportingConfig]
    TypeAlias: str = 'gt.powermeter.reporting.config.100'

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        eq_reporting_config_list = []
        for elt in self.EqReportingConfigList:
            eq_reporting_config_list.append(elt.asdict())
        d["EqReportingConfigList"] = eq_reporting_config_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if not isinstance(self.ReportingPeriodS, int):
            errors.append(f"ReportingPeriodS {self.ReportingPeriodS} must have type int.")
        if not isinstance(self.PollPeriodMs, int):
            errors.append(f"PollPeriodMs {self.PollPeriodMs} must have type int.")
        if not isinstance(self.EqReportingConfigList, list):
            errors.append(f"EqReportingConfigList {self.EqReportingConfigList} must have type list.")
        else:
            for elt in self.EqReportingConfigList:
                if not isinstance(elt, GtEqReportingConfig):
                    errors.append(f"{elt} of self.EqReportingConfigList must have typeGtEqReportingConfig")
        if self.TypeAlias != 'gt.powermeter.reporting.config.100':
            errors.append(f"Type requires TypeAlias of gt.powermeter.reporting.config.100, not {self.TypeAlias}.")

        return errors
