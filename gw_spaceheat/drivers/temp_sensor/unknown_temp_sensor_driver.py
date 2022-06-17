
from data_classes.components.temp_sensor_component import TempSensorComponent
from drivers.temp_sensor.temp_sensor_driver import TempSensorDriver
from schema.enums.make_model.make_model_map import MakeModel


class UnknownTempSensorDriver(TempSensorDriver):

    def __init__(self, component: TempSensorComponent):
        super(UnknownTempSensorDriver, self).__init__(component=component)
        if component.cac.make_model != MakeModel.UNKNOWNMAKE__UNKNOWNMODEL:
            raise Exception(f"Expected {MakeModel.UNKNOWNMAKE__UNKNOWNMODEL}, got {component.cac}")

    def read_temp(self):
        raise NotImplementedError("UnknownTempSensorDriver!")
