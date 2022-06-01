import platform
from data_classes.sh_node import ShNode
from data_classes.cacs.temp_sensor_cac import TempSensorCac
from actors.strategy_switcher import main as strategy_switcher
import load_house


if platform.platform() == 'Linux-4.19.118-v7l+-armv7l-with-glibc2.28':
    load_house.load_all(house_json_file='input_data/pi_dev_house.json')
else:
    load_house.load_all(house_json_file='input_data/dev_house.json')

nodes_w_components = list(filter(lambda x: x.primary_component_id is not None, ShNode.by_alias.values()))
actor_nodes_w_components = list(filter(lambda x: x.python_actor_name is not None, nodes_w_components))
temp_sensor_nodes = list(filter(lambda x: isinstance(x.primary_component.cac, TempSensorCac), actor_nodes_w_components))

for node in temp_sensor_nodes:
    (actor_function, keys) = strategy_switcher(node.python_actor_name)
    sensor = actor_function(node)