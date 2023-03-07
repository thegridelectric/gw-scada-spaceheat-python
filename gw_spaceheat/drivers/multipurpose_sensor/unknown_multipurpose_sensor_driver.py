from typing import Dict
from typing import List

from result import Result

from actors.config import ScadaSettings
from data_classes.components.multipurpose_sensor_component import (
    MultipurposeSensorComponent,
)
from drivers.driver_result import DriverResult
from drivers.multipurpose_sensor.multipurpose_sensor_driver import TelemetrySpec
from schema.enums import MakeModel

from drivers.multipurpose_sensor.multipurpose_sensor_driver import (
    MultipurposeSensorDriver,
)


class UnknownMultipurposeSensorDriver(MultipurposeSensorDriver):
    def __init__(self, component: MultipurposeSensorComponent, settings: ScadaSettings):
        super(UnknownMultipurposeSensorDriver, self).__init__(
            component=component, settings=settings
        )

    def __repr__(self):
        return "UnknownMultipurposeSensorDriver"

    def read_telemetry_values(self, channel_telemetry_list: List[TelemetrySpec]) -> Result[
            DriverResult[Dict[TelemetrySpec, int]], Exception]:
        pass
