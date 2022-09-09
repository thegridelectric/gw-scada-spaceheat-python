import json
from typing import Dict
from config import ScadaSettings

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


def load_cacs(dna):
    for d in dna["BooleanActuatorCacs"]:
        GtBooleanActuatorCac_Maker.dict_to_dc(d)
    for d in dna["ResistiveHeaterCacs"]:
        ResistiveHeaterCacGt_Maker.dict_to_dc(d)
    for d in dna["ElectricMeterCacs"]:
        GtElectricMeterCac_Maker.dict_to_dc(d)
    for d in dna["PipeFlowSensorCacs"]:
        GtPipeFlowSensorCac_Maker.dict_to_dc(d)
    for d in dna["TempSensorCacs"]:
        GtTempSensorCac_Maker.dict_to_dc(d)
    for d in dna["OtherCacs"]:
        ComponentAttributeClass(component_attribute_class_id=d["ComponentAttributeClassId"])


def load_components(dna):
    for d in dna["BooleanActuatorComponents"]:
        GtBooleanActuatorComponent_Maker.dict_to_dc(d)
    for d in dna["ResistiveHeaterComponents"]:
        ResistiveHeaterComponentGt_Maker.dict_to_dc(d)
    for d in dna["ElectricMeterComponents"]:
        GtElectricMeterComponent_Maker.dict_to_dc(d)
    for d in dna["PipeFlowSensorComponents"]:
        GtPipeFlowSensorComponent_Maker.dict_to_dc(d)
    for d in dna["TempSensorComponents"]:
        GtTempSensorComponent_Maker.dict_to_dc(d)
    for camel in dna["OtherComponents"]:
        snake_dict = {camel_to_snake(k): v for k, v in camel.items()}
        Component(**snake_dict)


def load_nodes(dna):
    for d in dna["ShNodes"]:
        SpaceheatNodeGt_Maker.dict_to_dc(d)


def load_all(settings: ScadaSettings):
    dna: Dict = json.loads(settings.dna_type)
    #TODO dna into GwTuple of a schema type with lots of consistency checking
    load_cacs(dna=dna)
    load_components(dna=dna)
    load_nodes(dna=dna)

