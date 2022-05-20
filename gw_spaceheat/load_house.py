import json
from utils import camel_to_snake

from data_classes.boolean_actuator_cac import BooleanActuatorCac
from data_classes.boolean_actuator_component import BooleanActuatorComponent
from data_classes.cac import Cac
from data_classes.component import Component
from data_classes.electric_heater_cac import ElectricHeaterCac
from data_classes.electric_heater_component import ElectricHeaterComponent
from data_classes.sensor_cac import SensorCac
from data_classes.sensor_component import SensorComponent
from data_classes.sh_node import ShNode
from data_classes.thermal_edge import ThermalEdge

HOUSE_JSON_FILE = 'input_data/dev_house.json'


def load_cacs(input_data):
    for camel in input_data['BooleanActuatorCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = BooleanActuatorCac(**snake_dict)
    for camel in input_data['ElectricHeaterCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricHeaterCac(**snake_dict)
    for camel in input_data['SensorCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = SensorCac(**snake_dict) 
    for camel in input_data['OtherCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = Cac(**snake_dict)      


def load_components(input_data):
    for camel in input_data['BooleanActuatorComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = BooleanActuatorComponent(**snake_dict)
    for camel in input_data['ElectricHeaterComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricHeaterComponent(**snake_dict)
    for camel in input_data['SensorComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = SensorComponent(**snake_dict)
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
    with open(house_json_file,"r") as read_file:
        input_data = json.load(read_file)
    load_cacs(input_data=input_data)
    load_components(input_data=input_data)
    load_nodes(input_data=input_data)
    load_edges(input_data=input_data)

