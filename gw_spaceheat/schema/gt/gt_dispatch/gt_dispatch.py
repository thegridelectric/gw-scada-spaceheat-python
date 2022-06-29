"""gt.dispatch.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_dispatch.gt_dispatch_base import GtDispatchBase


class GtDispatch(GtDispatchBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.dispatch for {self}: {errors}")

    def hand_coded_errors(self):
        return []
