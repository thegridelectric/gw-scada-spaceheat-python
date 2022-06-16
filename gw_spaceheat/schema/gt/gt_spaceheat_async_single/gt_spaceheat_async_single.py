"""gt.spaceheat.async.single.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_spaceheat_async_single.gt_spaceheat_async_single_base import GtSpaceheatAsyncSingleBase


class GtSpaceheatAsyncSingle(GtSpaceheatAsyncSingleBase):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.spaceheat.async.single for {self}: {errors}")

    def hand_coded_errors(self):
        return []
