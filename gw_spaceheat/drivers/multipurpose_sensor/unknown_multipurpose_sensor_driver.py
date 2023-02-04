from typing import Optional

from actors2.config import ScadaSettings
from data_classes.components.multipurpose_sensor_component import (
    MultipurposeSensorComponent,
)
from schema.enums import MakeModel

from drivers.multipurpose_sensor.multipurpose_sensor_driver import (
    MultipurposeSensorDriver,
)


class UnknownMultipurposeSensorDriver(MultipurposeSensorDriver):
    def __init__(self, component: MultipurposeSensorComponent, settings: ScadaSettings):
        super(UnknownMultipurposeSensorDriver, self).__init__(
            component=component, settings=settings
        )
        if component.cac.make_model != MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            raise Exception(
                f"Expected {MakeModel.UNKNOWNMAKE__UNKNOWNMODEL}, got {component.cac}"
            )

    def __repr__(self):
        return "UnknownMultipurposeSensorDriver"

    def read_telemetry_value(self) -> Optional[int]:
        return None
