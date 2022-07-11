"""resistive.heater.component.gt.100 type"""

from schema.errors import MpSchemaError
from schema.gt.resistive_heater_component_gt.resistive_heater_component_gt_base import (
    ResistiveHeaterComponentGtBase,
)


class ResistiveHeaterComponentGt(ResistiveHeaterComponentGtBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making resistive.heater.component.gt.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
