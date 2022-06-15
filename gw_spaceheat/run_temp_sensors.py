import platform
from data_classes.sh_node import ShNode
from actors.strategy_switcher import strategy_from_node
import load_house
from schema.enums.role.role_map import Role


if platform.platform() == 'Linux-4.19.118-v7l+-armv7l-with-glibc2.28':
    load_house.load_all(house_json_file='input_data/pi_dev_house.json')
else:
    load_house.load_all(house_json_file='input_data/dev_house.json')

all_nodes = list(ShNode.by_alias.values())
tank_water_temp_sensor_nodes = list(filter(lambda x: x.role == Role.TANK_WATER_TEMP_SENSOR, all_nodes))


for node in tank_water_temp_sensor_nodes:
    actor_function = strategy_from_node(node)
    if not actor_function:
        raise Exception(f"Expected strategy for {node}!")
    sensor = actor_function(node)
