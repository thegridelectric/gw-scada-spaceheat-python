"""GridWorks serial message protocol gs.pwr.100 with MpAlias p"""
from schema.errors import MpSchemaError
from schema.gs.gs_pwr_base import GsPwrBase


class GsPwr(GsPwrBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gs.pwr.100 for {self}: {errors}")

    def hand_coded_errors(self):
        return []
