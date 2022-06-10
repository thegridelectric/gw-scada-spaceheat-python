import json
import os

from schema.gt.gt_boolean_actuator_cac.gt_boolean_actuator_cac_maker import GtBooleanActuatorCac_Maker
from schema.gt.gt_electric_heater_cac.gt_electric_heater_cac_maker import GtElectricHeaterCac_Maker
from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import GtElectricMeterCac_Maker
from schema.gt.gt_pipe_flow_sensor_cac.gt_pipe_flow_sensor_cac_maker import GtPipeFlowSensorCac_Maker
from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac_maker import GtTempSensorCac_Maker
from schema.gt.gt_boolean_actuator_component.gt_boolean_actuator_component_maker import GtBooleanActuatorComponent_Maker
from schema.gt.gt_electric_heater_component.gt_electric_heater_component_maker import GtElectricHeaterComponent_Maker
from schema.gt.gt_electric_meter_component.gt_electric_meter_component_maker import GtElectricMeterComponent_Maker
from schema.gt.gt_pipe_flow_sensor_component.gt_pipe_flow_sensor_component_maker import GtPipeFlowSensorComponent_Maker
from schema.gt.gt_temp_sensor_component.gt_temp_sensor_component_maker import GtTempSensorComponent_Maker

from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.components.boolean_actuator_component import \
    BooleanActuatorComponent
from data_classes.components.electric_heater_component import \
    ElectricHeaterComponent
from data_classes.components.electric_meter_component import \
    ElectricMeterComponent
from data_classes.components.pipe_flow_sensor_component import \
    PipeFlowSensorComponent
from data_classes.components.temp_sensor_component import TempSensorComponent
from data_classes.sh_node import ShNode

from helpers import camel_to_snake

HOUSE_JSON_FILE = 'input_data/dev_house.json'


def load_cacs(input_data):
    for d in input_data['BooleanActuatorCacs']:
        GtBooleanActuatorCac_Maker.dict_to_tuple(d)
    for d in input_data['ElectricHeaterCacs']:
        GtElectricHeaterCac_Maker.dict_to_tuple(d)
    for d in input_data['ElectricMeterCacs']:
        GtElectricMeterCac_Maker.dict_to_tuple(d)
    for d in input_data['PipeFlowSensorCacs']:
        GtPipeFlowSensorCac_Maker.dict_to_tuple(d)
    for d in input_data['TempSensorCacs']:
        GtTempSensorCac_Maker.dict_to_tuple(d)
    for d in input_data['OtherCacs']:
        ComponentAttributeClass(component_attribute_class_id=d["ComponentAttributeClassId"])


def load_components(input_data):
    for d in input_data['BooleanActuatorComponents']:
        GtBooleanActuatorComponent_Maker.dict_to_tuple(d)
    for d in input_data['ElectricHeaterComponents']:
        GtElectricHeaterComponent_Maker.dict_to_tuple(d)
    for d in input_data['ElectricMeterComponents']:
        GtElectricMeterComponent_Maker.dict_to_tuple(d)
    for d in input_data['PipeFlowSensorComponents']:
        GtPipeFlowSensorComponent_Maker.dict_to_tuple(d)
    for d in input_data['TempSensorComponents']:
        GtTempSensorComponent_Maker.dict_to_tuple(d)
    for camel in input_data['OtherComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        Component(**snake_dict)
    

def load_nodes(input_data):
    for camel in input_data['ShNodes']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        node = ShNode(**snake_dict)


def load_edges(input_data):
    pass


def load_all(house_json_file=HOUSE_JSON_FILE):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, house_json_file), "r") as read_file:
        input_data = json.load(read_file)
    load_cacs(input_data=input_data)
    load_components(input_data=input_data)
    load_nodes(input_data=input_data)
    load_edges(input_data=input_data)

