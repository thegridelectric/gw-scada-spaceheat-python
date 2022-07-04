"""gt.driver.booleanactuator.cmd.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_driver_booleanactuator_cmd.gt_driver_booleanactuator_cmd_base import (
    GtDriverBooleanactuatorCmdBase,
)


class GtDriverBooleanactuatorCmd(GtDriverBooleanactuatorCmdBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.driver.booleanactuator.cmd.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
