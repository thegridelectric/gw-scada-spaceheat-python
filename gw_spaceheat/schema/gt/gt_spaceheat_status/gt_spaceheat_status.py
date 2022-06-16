"""gt.spaceheat.status type"""

from schema.errors import MpSchemaError
from schema.gt.gt_spaceheat_status.gt_spaceheat_status_base import GtSpaceheatStatusBase


class GtSpaceheatStatus(GtSpaceheatStatusBase):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.spaceheat.status: {errors}")

    def hand_coded_errors(self):
        return []
