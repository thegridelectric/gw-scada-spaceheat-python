"""GridWorks serial message protocol GsPwr100 with MpAlias d"""
from schema.errors import MpSchemaError
from schema.gs.gs_dispatch_base import GsDispatchBase

class GsDispatch(GsDispatchBase):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gs.pwr.100 for {self}: {errors}")

    def hand_coded_errors(self):
        return []