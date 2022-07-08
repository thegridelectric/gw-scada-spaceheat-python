"""Test load_house module"""

import json
import os

import load_house
from data_classes.sh_node import ShNode
from schema.enums.role.sh_node_role_110 import Role
from schema.gt.gt_sh_node.gt_sh_node_maker import GtShNode_Maker


def test_load_real_house():
    real_world_root_alias = "w"
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(
        os.path.join(current_dir, "../gw_spaceheat/input_data/houses.json"), "r"
    ) as read_file:
        input_data = json.load(read_file)
    house_data = input_data[real_world_root_alias]
    for d in house_data["ShNodes"]:
        GtShNode_Maker.dict_to_tuple(d)
    for node in ShNode.by_alias.values():
        print(node.parent)


def test_load_house():
    """Verify that load_house() successfully loads test objects"""
    load_house.load_all()
    for node in ShNode.by_alias.values():
        print(node.parent)
    all_nodes = list(ShNode.by_alias.values())
    assert len(all_nodes) == 24
    aliases = list(ShNode.by_alias.keys())
    for i in range(len(aliases)):
        alias = aliases[i]
        node = ShNode.by_alias[alias]
        print(node)
    nodes_w_components = list(
        filter(lambda x: x.component_id is not None, ShNode.by_alias.values())
    )
    assert len(nodes_w_components) == 18
    actor_nodes_w_components = list(filter(lambda x: x.has_actor, nodes_w_components))
    assert len(actor_nodes_w_components) == 12
    tank_water_temp_sensor_nodes = list(
        filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes)
    )
    assert len(tank_water_temp_sensor_nodes) == 5
    for node in tank_water_temp_sensor_nodes:
        assert node.reporting_sample_period_s is not None
