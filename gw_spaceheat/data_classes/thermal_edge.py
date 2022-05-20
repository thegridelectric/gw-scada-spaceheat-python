from typing import NamedTuple
from data_classes.sh_node import ShNode

class ThermalEdge(NamedTuple):
    FromNode: ShNode
    ToNode: ShNode