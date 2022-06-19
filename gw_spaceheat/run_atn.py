import load_house
from data_classes.sh_node import ShNode
from actors.atn import Atn

load_house.load_all(input_json_file='input_data/houses.json')
node = ShNode.by_alias['a']
atn = Atn(node)
atn.start()