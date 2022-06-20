import load_house
from actors.boolean_actuator import BooleanActuator
from data_classes.sh_node import ShNode

load_house.load_all(input_json_file="input_data/houses.json")
node = ShNode.by_alias["a.elt1.relay"]
boost = BooleanActuator(node, logging_on=True)

boost.start()