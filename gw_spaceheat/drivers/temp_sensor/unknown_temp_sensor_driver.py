from typing import Optional
from actors2.config import ScadaSettings
from data_classes.components.temp_sensor_component import TempSensorComponent
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.enums import MakeModel


class UnknownTempSensorDriver(TempSensorDriver):
    def __init__(self, component: TempSensorComponent, settings: ScadaSettings):
        super(UnknownTempSensorDriver, self).__init__(component=component, settings=settings)
        if component.cac.make_model != MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            raise Exception(f"Expected {MakeModel.UNKNOWNMAKE__UNKNOWNMODEL}, got {component.cac}")

    def __repr__(self):
        return "UnknownTempSensorDriver"

    def read_telemetry_value(self) -> Optional[int]:
        return None
