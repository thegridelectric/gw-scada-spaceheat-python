"""gt.boolean.actuator.component.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_boolean_actuator_component.gt_boolean_actuator_component_base import (
    GtBooleanActuatorComponentBase,
)


class GtBooleanActuatorComponent(GtBooleanActuatorComponentBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.boolean.actuator.component.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
