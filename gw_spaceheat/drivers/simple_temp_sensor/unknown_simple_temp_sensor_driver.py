from typing import Optional
from actors2.config import ScadaSettings
from data_classes.components.simple_temp_sensor_component import SimpleTempSensorComponent
from drivers.simple_temp_sensor.simple_temp_sensor_driver import SimpleTempSensorDriver
from schema.enums import MakeModel


class UnknownSimpleTempSensorDriver(SimpleTempSensorDriver):
    def __init__(self, component: SimpleTempSensorComponent, settings: ScadaSettings):
        super(UnknownSimpleTempSensorDriver, self).__init__(component=component, settings=settings)
        if component.cac.make_model != MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            raise Exception(f"Expected {MakeModel.UNKNOWNMAKE__UNKNOWNMODEL}, got {component.cac}")

    def __repr__(self):
        return "UnknownSimpleTempSensorDriver"

    def read_telemetry_value(self) -> Optional[int]:
        return None
