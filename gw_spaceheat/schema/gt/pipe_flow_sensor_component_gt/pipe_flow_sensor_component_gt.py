"""pipe.flow.sensor.component.gt.000 type"""

from schema.errors import MpSchemaError
from schema.gt.pipe_flow_sensor_component_gt.pipe_flow_sensor_component_gt_base import (
    PipeFlowSensorComponentGtBase,
)


class PipeFlowSensorComponentGt(PipeFlowSensorComponentGtBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making pipe.flow.sensor.component.gt.000 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
