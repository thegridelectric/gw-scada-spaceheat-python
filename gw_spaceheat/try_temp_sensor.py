import platform
from data_classes.sh_node import ShNode
from actors.strategy_switcher import main as strategy_switcher
import load_house

if platform.platform() == 'Linux-4.19.118-v7l+-armv7l-with-glibc2.28':
    load_house.load_all(house_json_file='input_data/pi_dev_house.json')
else:
    load_house.load_all(house_json_file='input_data/dev_house.json')

node = ShNode.by_alias["a.tank.temp0"]

(actor_function, keys) = strategy_switcher(node.python_actor_name)
sensor = actor_function(node)
