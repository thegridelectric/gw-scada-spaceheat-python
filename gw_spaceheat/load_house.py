import json
import os

import settings
from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from helpers import camel_to_snake
from schema.gt.gt_boolean_actuator_cac.gt_boolean_actuator_cac_maker import (
    GtBooleanActuatorCac_Maker,
)
from schema.gt.gt_boolean_actuator_component.gt_boolean_actuator_component_maker import (
    GtBooleanActuatorComponent_Maker,
)

from schema.gt.resistive_heater_cac_gt.resistive_heater_cac_gt_maker import ResistiveHeaterCacGt_Maker
from schema.gt.resistive_heater_component_gt.resistive_heater_component_gt_maker import (
    ResistiveHeaterComponentGt_Maker,
)

from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import GtElectricMeterCac_Maker
from schema.gt.gt_electric_meter_component.gt_electric_meter_component_maker import (
    GtElectricMeterComponent_Maker,
)
from schema.gt.gt_pipe_flow_sensor_cac.gt_pipe_flow_sensor_cac_maker import (
    GtPipeFlowSensorCac_Maker,
)
from schema.gt.gt_pipe_flow_sensor_component.gt_pipe_flow_sensor_component_maker import (
    GtPipeFlowSensorComponent_Maker,
)
from schema.gt.spaceheat_node_gt.spaceheat_node_gt_maker import SpaceheatNodeGt_Maker
from schema.gt.gt_temp_sensor_cac.gt_temp_sensor_cac_maker import GtTempSensorCac_Maker
from schema.gt.gt_temp_sensor_component.gt_temp_sensor_component_maker import (
    GtTempSensorComponent_Maker,
)

INPUT_JSON_FILE = "input_data/houses.json"


def load_cacs(house_data):
    for d in house_data["BooleanActuatorCacs"]:
        GtBooleanActuatorCac_Maker.dict_to_dc(d)
    for d in house_data["ResistiveHeaterCacs"]:
        ResistiveHeaterCacGt_Maker.dict_to_dc(d)
    for d in house_data["ElectricMeterCacs"]:
        GtElectricMeterCac_Maker.dict_to_dc(d)
    for d in house_data["PipeFlowSensorCacs"]:
        GtPipeFlowSensorCac_Maker.dict_to_dc(d)
    for d in house_data["TempSensorCacs"]:
        GtTempSensorCac_Maker.dict_to_dc(d)
    for d in house_data["OtherCacs"]:
        ComponentAttributeClass(component_attribute_class_id=d["ComponentAttributeClassId"])


def load_components(house_data):
    for d in house_data["BooleanActuatorComponents"]:
        GtBooleanActuatorComponent_Maker.dict_to_dc(d)
    for d in house_data["ResistiveHeaterComponents"]:
        ResistiveHeaterComponentGt_Maker.dict_to_dc(d)
    for d in house_data["ElectricMeterComponents"]:
        GtElectricMeterComponent_Maker.dict_to_dc(d)
    for d in house_data["PipeFlowSensorComponents"]:
        GtPipeFlowSensorComponent_Maker.dict_to_dc(d)
    for d in house_data["TempSensorComponents"]:
        GtTempSensorComponent_Maker.dict_to_dc(d)
    for camel in house_data["OtherComponents"]:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        Component(**snake_dict)


def load_nodes(house_data):
    for d in house_data["ShNodes"]:
        SpaceheatNodeGt_Maker.dict_to_dc(d)


def load_all(world_root_alias=settings.WORLD_ROOT_ALIAS):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, "input_data/houses.json"), "r") as read_file:
        input_data = json.load(read_file)
    if world_root_alias not in input_data.keys():
        raise Exception(f"{world_root_alias} house data missing from input_data/houses.json")
    house_data = input_data[world_root_alias]
    load_cacs(house_data=house_data)
    load_components(house_data=house_data)
    load_nodes(house_data=house_data)


def stickler():
    return
