import sys
import time
from typing import List, Optional

import dotenv

import load_house
from command_line_utils import run_nodes_main, parse_args
from config import ScadaSettings
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role


def get_single_node(nodes: dict) -> Optional[ShNode]:
    node_alias = input("Node alias? ")
    if node_alias not in nodes.keys():
        print(f"Do not recognize {node_alias}! Please pick from this list:")
        for alias in nodes.keys():
            print(alias)
        return None
    return nodes[node_alias]


def add_all_nodes_of_role(node_alias_list: List, role: Role, nodes: dict) -> List:
    all_nodes = list(nodes.values())
    role_nodes = list(filter(lambda x: (x.role == role and x.has_actor), all_nodes))
    for node in role_nodes:
        node_alias_list.append(node.alias)
    return node_alias_list


def get_role() -> Optional[Role]:
    role_value = input("Role? ")
    try:
        Role(role_value)
    except ValueError:
        print(f"Do not recognize {role_value}! Please pick from this list:")
        for value in Role.values():
            print(value)
        return None
    return Role(role_value)


def get_y_n(response) -> Optional[bool]:
    if len(response) == 0:
        return None
    try:
        r = response.lower()
    except SyntaxError:
        print("Please enter y or n")
        return None
    if r[0] == "y":
        return True
    else:
        return False


def start_singles(node_alias_list: List, nodes: dict) -> List:
    starting_singles = True
    while starting_singles:
        response = input("Start single node (y,n)? ")
        single_start = get_y_n(response)
        if single_start is True:
            node = get_single_node(nodes)
            if node:
                node_alias_list.append(node.alias)
        else:
            starting_singles = False
        time.sleep(0.5)
    return node_alias_list


def start_roles(node_alias_list: List, nodes: dict) -> List:
    response = input("Start all TankWaterTempSensors? ")
    start_tank_water_temp_sensors = get_y_n(response)
    if start_tank_water_temp_sensors:
        node_alias_list = add_all_nodes_of_role(node_alias_list, Role.TANK_WATER_TEMP_SENSOR, nodes)

    response = input("Start all BooleanActuators? ")
    start_tank_water_temp_sensors = get_y_n(response)
    if start_tank_water_temp_sensors:
        node_alias_list = add_all_nodes_of_role(node_alias_list, Role.BOOLEAN_ACTUATOR, nodes)

    starting_roles = True
    while starting_roles:
        response = input("Start all actors of some other role? ")
        start_role = get_y_n(response)
        if start_role is True:
            role = get_role()
            if role:
                node_alias_list = add_all_nodes_of_role(node_alias_list, role, nodes)
        else:
            starting_roles = False
    return node_alias_list


def main():
    args = parse_args(sys.argv[1:])
    settings = ScadaSettings(_env_file=dotenv.find_dotenv(args.env_file))
    layout = load_house.load_all(settings)
    node_alias_list = []
    node_alias_list = start_singles(node_alias_list, layout.nodes)
    node_alias_list = start_roles(node_alias_list, layout.nodes)
    node_alias_list = sorted(list(set(node_alias_list)))

    print("About to start these actors:")
    print("")
    for alias in node_alias_list:
        print(alias)

    time.sleep(4)

    run_nodes_main(default_nodes=node_alias_list)


if __name__ == "__main__":
    main()
