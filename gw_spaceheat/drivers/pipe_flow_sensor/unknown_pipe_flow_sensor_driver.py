from typing import Optional
from data_classes.components.pipe_flow_sensor_component import PipeFlowSensorComponent
from drivers.pipe_flow_sensor.pipe_flow_sensor_driver import PipeFlowSensorDriver
from schema.enums.make_model.make_model_map import MakeModel


class UnknownPipeFlowSensorDriver(PipeFlowSensorDriver):

    def __init__(self, component: PipeFlowSensorComponent):
        super(UnknownPipeFlowSensorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            raise Exception(f"Expected {MakeModel.UNKNOWNMAKE__UNKNOWNMODEL}, got {component.cac}")

    def __repr__(self):
        return "UnknownPipeFlowSensorDriver"

    def read_telemetry_value(self) -> Optional[int]:
        return None
