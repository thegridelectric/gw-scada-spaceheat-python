"""Base for gt.powermeter.reporting.config.100"""
import json
from typing import List, NamedTuple, Optional
from schema.gt.gt_eq_reporting_config.gt_eq_reporting_config_maker import GtEqReportingConfig


class GtPowermeterReportingConfigBase(NamedTuple):
    ReportingPeriodS: int  #
    ElectricalQuantityReportingConfigList: List[GtEqReportingConfig]
    PollPeriodMs: int  #
    HwUid: Optional[str] = None
    TypeAlias: str = "gt.powermeter.reporting.config.100"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()
        if d["HwUid"] is None:
            del d["HwUid"]

        # Recursively call asdict() for the SubTypes
        electrical_quantity_reporting_config_list = []
        for elt in self.ElectricalQuantityReportingConfigList:
            electrical_quantity_reporting_config_list.append(elt.asdict())
        d["ElectricalQuantityReportingConfigList"] = electrical_quantity_reporting_config_list
        return d

    def derived_errors(self) -> List[str]:
        errors = []
        if self.HwUid:
            if not isinstance(self.HwUid, str):
                errors.append(
                    f"HwUid {self.HwUid} must have type str."
                )
        if not isinstance(self.ReportingPeriodS, int):
            errors.append(
                f"ReportingPeriodS {self.ReportingPeriodS} must have type int."
            )
        if not isinstance(self.ElectricalQuantityReportingConfigList, list):
            errors.append(
                f"ElectricalQuantityReportingConfigList {self.ElectricalQuantityReportingConfigList} must have type list."
            )
        else:
            for elt in self.ElectricalQuantityReportingConfigList:
                if not isinstance(elt, GtEqReportingConfig):
                    errors.append(
                        f"elt {elt} of ElectricalQuantityReportingConfigList must have type GtEqReportingConfig."
                    )
        if not isinstance(self.PollPeriodMs, int):
            errors.append(
                f"PollPeriodMs {self.PollPeriodMs} must have type int."
            )
        if self.TypeAlias != "gt.powermeter.reporting.config.100":
            errors.append(
                f"Type requires TypeAlias of gt.powermeter.reporting.config.100, not {self.TypeAlias}."
            )

        return errors
