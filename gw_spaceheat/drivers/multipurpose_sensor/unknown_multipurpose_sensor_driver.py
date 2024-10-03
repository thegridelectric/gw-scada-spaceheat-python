from typing import Dict
from typing import List

from gwproto.data_classes.components import Ads111xBasedComponent
from result import Result

from actors.config import ScadaSettings
from drivers.driver_result import DriverResult
from drivers.multipurpose_sensor.multipurpose_sensor_driver import TelemetrySpec

from drivers.multipurpose_sensor.multipurpose_sensor_driver import (
    MultipurposeSensorDriver,
)


class UnknownMultipurposeSensorDriver(MultipurposeSensorDriver):
    def __init__(self, component: Ads111xBasedComponent, settings: ScadaSettings):
        super().__init__(
            component=component, settings=settings
        )

    def __repr__(self):
        return "UnknownMultipurposeSensorDriver"

    def read_telemetry_values(self, channel_telemetry_list: List[TelemetrySpec]) -> Result[
            DriverResult[Dict[TelemetrySpec, int]], Exception]:
        pass
