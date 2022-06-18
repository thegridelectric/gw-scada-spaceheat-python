"""gt.sh.simple.status.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_sh_simple_status.gt_sh_simple_status_base \
    import GtShSimpleStatusBase


class GtShSimpleStatus(GtShSimpleStatusBase):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.sh.simple.status.100: {errors}")

    def hand_coded_errors(self):
        return []
