import load_house
from actors.atn import Atn
from data_classes.sh_node import ShNode

load_house.load_all()
node = ShNode.by_alias["a"]
atn = Atn(node)
atn.start()
