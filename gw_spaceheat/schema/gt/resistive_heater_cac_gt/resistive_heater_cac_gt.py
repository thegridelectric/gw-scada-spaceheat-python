"""resistive.heater.cac.gt.100 type"""

from schema.errors import MpSchemaError
from schema.gt.resistive_heater_cac_gt.resistive_heater_cac_gt_base import (
    ResistiveHeaterCacGtBase,
)


class ResistiveHeaterCacGt(ResistiveHeaterCacGtBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making resistive.heater.cac.gt.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
