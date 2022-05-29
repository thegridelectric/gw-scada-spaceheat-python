import json
import os

from data_classes.cacs.boolean_actuator_cac import BooleanActuatorCac
from data_classes.cacs.electric_heater_cac import ElectricHeaterCac
from data_classes.cacs.electric_meter_cac import ElectricMeterCac
from data_classes.cacs.pipe_flow_sensor_cac import PipeFlowSensorCac
from data_classes.cacs.temp_sensor_cac import TempSensorCac
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
    for camel in input_data['BooleanActuatorCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = BooleanActuatorCac(**snake_dict)
    for camel in input_data['ElectricHeaterCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricHeaterCac(**snake_dict)
    for camel in input_data['ElectricMeterCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricMeterCac(**snake_dict)
    for camel in input_data['TempSensorCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = TempSensorCac(**snake_dict) 
    for camel in input_data['PipeFlowSensorCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = PipeFlowSensorCac(**snake_dict) 
    for camel in input_data['OtherCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ComponentAttributeClass(**snake_dict)      


def load_components(input_data):
    for camel in input_data['BooleanActuatorComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = BooleanActuatorComponent(**snake_dict)
    for camel in input_data['ElectricHeaterComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricHeaterComponent(**snake_dict)
    for camel in input_data['ElectricMeterComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricMeterComponent(**snake_dict)
    for camel in input_data['TempSensorComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = TempSensorComponent(**snake_dict)
    for camel in input_data['PipeFlowSensorComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = PipeFlowSensorComponent(**snake_dict)
    for camel in input_data['OtherComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = Component(**snake_dict)
    

def load_nodes(input_data):
    for camel in input_data['ShNodes']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        node = ShNode(**snake_dict)

def load_edges(input_data):
    #Preethi TODO: want a list of thermal edges. Every time 
    # a new thermal edge is made it goes into this list.
    pass

def load_all(house_json_file=HOUSE_JSON_FILE):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, house_json_file), "r") as read_file:
        input_data = json.load(read_file)
    load_cacs(input_data=input_data)
    load_components(input_data=input_data)
    load_nodes(input_data=input_data)
    load_edges(input_data=input_data)

