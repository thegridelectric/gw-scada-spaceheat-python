"""gt.sh.status.110 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_sh_status.gt_sh_status_base import (
    GtShStatusBase,
)


class GtShStatus(GtShStatusBase):
    """Designed for the SCADA to send to the AtomicTNode every 5 minutes,
    for supporting an AtomicTNode with the incremental state data needed for deciding
    when to charge the big heating loads (boost elements, heat pumps)."""

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.sh.status.110 for {self}: {errors}")

    def hand_coded_errors(self):
        if self.ReportingPeriodS != 300:
            return ["ReportingPeriodS must be 300"]
        else:
            return []
