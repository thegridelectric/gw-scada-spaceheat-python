"""multipurpose.sensor.cac.gt.000 type"""

from schema.errors import MpSchemaError
from schema.gt.multipurpose_sensor_cac_gt.multipurpose_sensor_cac_gt_base import (
    MultipurposeSensorCacGtBase,
)


class MultipurposeSensorCacGt(MultipurposeSensorCacGtBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making simple.temp.sensor.cac.gt.000 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
