"""gt.powermeter.reporting.config.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_powermeter_reporting_config.gt_powermeter_reporting_config_base import (
    GtPowermeterReportingConfigBase,
)


class GtPowermeterReportingConfig(GtPowermeterReportingConfigBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.poll_more_than_reporting_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.powermeter.reporting.config for {self}: {errors}"
            )

    def poll_more_than_reporting_errors(self) -> list:
        """PollPeriodMs must be less than ReportingPeriodMs. PollPeriodMs is how frequently data is polled
        from the meter. ReportingPeriodMs is the synchronous report to the scada."""

        if self.PollPeriodMs < 1000 * self.ReportingPeriodS:
            return []
        else:
            return [
                f"Error! self.PollPeriodMs {self.PollPeriodMs} is greater than "
                f"1000 * ReportingPeriodS (1000 * {self.ReportingPeriodS})"
            ]
