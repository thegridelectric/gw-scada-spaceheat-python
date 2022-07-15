"""Test load_house module"""

import json
import os

from config import ScadaSettings
from test.utils import flush_all
import load_house

from data_classes.component import Component
from data_classes.component_attribute_class import ComponentAttributeClass
from data_classes.components.boolean_actuator_component import (
    BooleanActuatorCac,
    BooleanActuatorComponent,
)
from data_classes.components.electric_meter_component import (
    ElectricMeterCac,
    ElectricMeterComponent,
)
from data_classes.components.pipe_flow_sensor_component import (
    PipeFlowSensorCac,
    PipeFlowSensorComponent,
)
from data_classes.components.resistive_heater_component import (
    ResistiveHeaterCac,
    ResistiveHeaterComponent,
)
from data_classes.components.temp_sensor_component import TempSensorCac, TempSensorComponent
from data_classes.sh_node import ShNode
from schema.enums.role.sh_node_role_110 import Role
from schema.gt.gt_electric_meter_cac.gt_electric_meter_cac_maker import GtElectricMeterCac_Maker
from schema.gt.gt_electric_meter_component.gt_electric_meter_component_maker import (
    GtElectricMeterComponent_Maker,
)
from schema.gt.spaceheat_node_gt.spaceheat_node_gt_maker import SpaceheatNodeGt_Maker


def test_load_real_house():
    real_world_root_alias = "w"
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(
        os.path.join(current_dir, "../gw_spaceheat/input_data/houses.json"), "r"
    ) as read_file:
        input_data = json.load(read_file)
    house_data = input_data[real_world_root_alias]
    for d in house_data["ShNodes"]:
        SpaceheatNodeGt_Maker.dict_to_tuple(d)
    for node in ShNode.by_alias.values():
        print(node.parent)


def test_flush_and_load_house():
    """Verify that flush_house() successfully removes all dictionary data from relevant dataclasses, and
    load_house() successfully loads test objects"""
    flush_all()

    unknown_electric_meter_cac_dict = {
        "ComponentAttributeClassId": "c1f17330-6269-4bc5-aa4b-82e939e9b70c",
        "MakeModelGtEnumSymbol": "b6a32d9b",
        "DisplayName": "Unknown Power Meter",
        "LocalCommInterfaceGtEnumSymbol": "829549d1",
        "TypeAlias": "gt.electric.meter.cac.100",
    }

    electric_meter_component_dict = {
        "ComponentId": "c7d352db-9a86-40f0-9601-d99243719cc5",
        "DisplayName": "Test unknown meter",
        "ComponentAttributeClassId": "c1f17330-6269-4bc5-aa4b-82e939e9b70c",
        "HwUid": "7ec4a224",
        "TypeAlias": "gt.electric.meter.component.100",
    }

    meter_node_dict = {
        "Alias": "a.m",
        "RoleGtEnumSymbol": "9ac68b6e",
        "ActorClassGtEnumSymbol": "2ea112b9",
        "DisplayName": "Main Power Meter Little Orange House Test System",
        "ShNodeId": "c9456f5b-5a39-4a48-bb91-742a9fdc461d",
        "ComponentId": "c7d352db-9a86-40f0-9601-d99243719cc5",
        "TypeAlias": "spaceheat.node.gt.100",
    }

    GtElectricMeterCac_Maker.dict_to_dc(unknown_electric_meter_cac_dict)
    GtElectricMeterComponent_Maker.dict_to_dc(electric_meter_component_dict)

    SpaceheatNodeGt_Maker.dict_to_dc(meter_node_dict)
    assert ShNode.by_alias["a.m"].sh_node_id == "c9456f5b-5a39-4a48-bb91-742a9fdc461d"
    flush_all()

    load_house.load_all(ScadaSettings().world_root_alias)
    assert ShNode.by_alias["a.m"].sh_node_id == "0dd8a803-4724-4f49-b845-14ff57bdb3e6"
    for node in ShNode.by_alias.values():
        print(node.parent)
    all_nodes = list(ShNode.by_alias.values())
    assert len(all_nodes) == 26
    aliases = list(ShNode.by_alias.keys())
    for i in range(len(aliases)):
        alias = aliases[i]
        node = ShNode.by_alias[alias]
        print(node)
    nodes_w_components = list(
        filter(lambda x: x.component_id is not None, ShNode.by_alias.values())
    )
    assert len(nodes_w_components) == 20
    actor_nodes_w_components = list(filter(lambda x: x.has_actor, nodes_w_components))
    assert len(actor_nodes_w_components) == 13
    tank_water_temp_sensor_nodes = list(
        filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes)
    )
    assert len(tank_water_temp_sensor_nodes) == 5
    for node in tank_water_temp_sensor_nodes:
        assert node.reporting_sample_period_s is not None

    flush_all()
    assert BooleanActuatorComponent.by_id == {}
    assert ElectricMeterComponent.by_id == {}
    assert PipeFlowSensorComponent.by_id == {}
    assert ResistiveHeaterComponent.by_id == {}
    assert TempSensorComponent.by_id == {}
    assert Component.by_id == {}

    assert BooleanActuatorCac.by_id == {}
    assert ElectricMeterCac.by_id == {}
    assert PipeFlowSensorCac.by_id == {}
    assert ResistiveHeaterCac.by_id == {}
    assert TempSensorCac.by_id == {}
    assert ComponentAttributeClass.by_id == {}
    assert ShNode.by_id == {}
    assert ShNode.by_alias == {}
