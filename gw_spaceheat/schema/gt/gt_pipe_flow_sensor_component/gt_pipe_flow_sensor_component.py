"""gt.pipe.flow.sensor.component.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_pipe_flow_sensor_component.gt_pipe_flow_sensor_component_base import (
    GtPipeFlowSensorComponentBase,
)


class GtPipeFlowSensorComponent(GtPipeFlowSensorComponentBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.pipe.flow.sensor.component.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
