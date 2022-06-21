import load_house
from actors.scada import Scada
from data_classes.sh_node import ShNode

load_house.load_all()
node = ShNode.by_alias["a.s"]
scada = Scada(node, logging_on=True)

scada.start()