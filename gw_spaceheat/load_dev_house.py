import json
from utils import camel_to_snake

from data_classes.actuator_cac import ActuatorCac
from data_classes.actuator_component import ActuatorComponent
from data_classes.cac import Cac
from data_classes.component import Component
from data_classes.electric_heater_cac import ElectricHeaterCac
from data_classes.electric_heater_component import ElectricHeaterComponent
from data_classes.sensor_cac import SensorCac
from data_classes.sensor_component import SensorComponent
from data_classes.sh_node import ShNode


REGISTRY_JSON_FILE = 'input_data/dev_house.json'


with open(REGISTRY_JSON_FILE,"r") as read_file:
    input_data = json.load(read_file)

def load_cacs():
    for camel in input_data['ActuatorCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ActuatorCac(**snake_dict)
    for camel in input_data['ElectricHeaterCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricHeaterCac(**snake_dict)
    for camel in input_data['SensorCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = SensorCac(**snake_dict) 
    for camel in input_data['OtherCacs']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = Cac(**snake_dict)      


def load_components():
    for camel in input_data['ActuatorComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ActuatorComponent(**snake_dict)
    for camel in input_data['ElectricHeaterComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = ElectricHeaterComponent(**snake_dict)
    for camel in input_data['SensorComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = SensorComponent(**snake_dict)
    for camel in input_data['OtherComponents']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        component = Component(**snake_dict)
    

def load_nodes():
    for camel in input_data['ShNodes']:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        node = ShNode(**snake_dict)

def load_all():
    load_cacs()
    load_components()
    load_nodes()

