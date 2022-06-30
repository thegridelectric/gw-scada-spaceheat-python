"""gt.sh.simple.single.status.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_sh_simple_single_status.gt_sh_simple_single_status_base import (
    GtShSimpleSingleStatusBase,
)


class GtShSimpleSingleStatus(GtShSimpleSingleStatusBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.sh.simple.single.status.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        errors = []
        if len(self.ValueList) != len(self.ReadTimeUnixMsList):
            errors.append("Length of ValueList and ReadTimeUnixMsList must be equal ")
        return errors
