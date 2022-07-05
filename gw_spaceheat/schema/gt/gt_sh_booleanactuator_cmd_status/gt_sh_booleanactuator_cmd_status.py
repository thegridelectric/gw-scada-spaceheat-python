"""gt.sh.booleanactuator.cmd.status.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_sh_booleanactuator_cmd_status.gt_sh_booleanactuator_cmd_status_base import (
    GtShBooleanactuatorCmdStatusBase,
)


class GtShBooleanactuatorCmdStatus(GtShBooleanactuatorCmdStatusBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.sh.booleanactuator.cmd.status.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
