"""gt.temp.sensor.cac.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac_100_base import GtTempSensorCac100Base


class GtTempSensorCac100(GtTempSensorCac100Base):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making gt.temp.sensor.cac.100 for {self}: {errors}")

    def hand_coded_errors(self):
        return []
