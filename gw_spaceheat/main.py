import platform

from data_classes.sh_node import ShNode
from actors.strategy_switcher import strategy_from_node
import load_house

if platform.system() == 'Darwin':
    house_json_file = 'input_data/dev_house.json'
else:
    house_json_file = 'input_data/pi_dev_house.json'

load_house.load_all(house_json_file=house_json_file)
node = ShNode.by_alias["a.s"]

actor_function = strategy_from_node(node)
if actor_function:
    scada = actor_function(node)
