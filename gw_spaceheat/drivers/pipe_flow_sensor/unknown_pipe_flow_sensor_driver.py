from typing import Optional

from actors2.config import ScadaSettings
from data_classes.components.pipe_flow_sensor_component import \
    PipeFlowSensorComponent
from drivers.pipe_flow_sensor.pipe_flow_sensor_driver import \
    PipeFlowSensorDriver
from schema.enums import MakeModel


class UnknownPipeFlowSensorDriver(PipeFlowSensorDriver):
    def __init__(self, component: PipeFlowSensorComponent, settings: ScadaSettings):
        super(UnknownPipeFlowSensorDriver, self).__init__(component=component, settings=settings)


    def __repr__(self):
        return "UnknownPipeFlowSensorDriver"

    def read_telemetry_value(self) -> Optional[int]:
        return None
