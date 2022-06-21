import time
from typing import List, Optional

import load_house
from actors.strategy_switcher import strategy_from_node
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role


def add_actor(actor_list: List, node: ShNode) -> List:
    actor_function = strategy_from_node(node)
    if not actor_function:
        print(f"Missing strategy for {node} in strategy_switcher")
        return actor_list
    actor = actor_function(node)
    existing_nodes = list(map(lambda x: x.node, actor_list))
    if actor.node not in existing_nodes:
        actor_list.append(actor)
    return actor_list


def get_single_node() -> Optional[ShNode]:
    node_alias = input("Node alias? ")
    if node_alias not in ShNode.by_alias.keys():
        print(f"Do not recognize {node_alias}! Please pick from this list:")
        for alias in ShNode.by_alias.keys():
            print(alias)
        return None
    return ShNode.by_alias[node_alias]


def add_all_nodes_of_role(actor_list: List, role: Role) -> List:
    all_nodes = list(ShNode.by_alias.values())
    role_nodes = list(filter(lambda x: (x.role == role and x.has_actor), all_nodes))
    for node in role_nodes:
        actor_list = add_actor(actor_list, node)
    return actor_list


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


def start_singles(actor_list) -> list:
    load_house.load_all()

    starting_singles = True
    while starting_singles:
        response = input("Start single node (y,n)? ")
        single_start = get_y_n(response)
        if single_start is True:
            node = get_single_node()
            if node:
                actor_list = add_actor(actor_list, node)
        else:
            starting_singles = False
        time.sleep(0.5)
    return actor_list


def start_roles(actor_list) -> List:
    response = input("Start all TankWaterTempSensors? ")
    start_tank_water_temp_sensors = get_y_n(response)
    if start_tank_water_temp_sensors:
        actor_list = add_all_nodes_of_role(actor_list, Role.TANK_WATER_TEMP_SENSOR)

    response = input("Start all BooleanActuators? ")
    start_tank_water_temp_sensors = get_y_n(response)
    if start_tank_water_temp_sensors:
        actor_list = add_all_nodes_of_role(actor_list, Role.BOOLEAN_ACTUATOR)

    starting_roles = True
    while starting_roles:
        response = input("Start all actors of some other role? ")
        start_role = get_y_n(response)
        if start_role is True:
            role = get_role()
            if role:
                actor_list = add_all_nodes_of_role(actor_list, role)
        else:
            starting_roles = False
    return actor_list


def main():
    actor_list = []
    actor_list = start_singles(actor_list)
    actor_list = start_roles(actor_list)
    actor_list = sorted(list(set(actor_list)), key=lambda x: x.node.alias)

    print("About to start these actors:")
    print("")
    for actor in actor_list:
        print(actor.node.alias)

    time.sleep(4)
    for actor in actor_list:
        actor.start()


if __name__ == "__main__":
    main()
