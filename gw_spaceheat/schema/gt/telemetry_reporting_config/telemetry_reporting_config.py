"""telemetry.reporting.config.000 type"""

from schema.errors import MpSchemaError
from schema.gt.telemetry_reporting_config.telemetry_reporting_config_base import  (
    TelemetryReportingConfigBase,
)


class TelemetryReportingConfig(TelemetryReportingConfigBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making telemetry.reporting.config.000 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
