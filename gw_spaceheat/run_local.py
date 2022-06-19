from actors.strategy_switcher import strategy_from_node
import load_house
from schema.enums.role.role_map import Role
from data_classes.sh_node import ShNode


load_house.load_all(input_json_file="input_data/houses.json")
all_nodes = list(ShNode.by_alias.values())
local_nodes = list(filter(lambda x: (x.role != Role.ATN and x.has_actor), all_nodes))

for node in local_nodes:
    actor_function = strategy_from_node(node)
    if not actor_function:
        raise Exception(f"Expected strategy for {node}!")
    actor = actor_function(node)
    actor.start()
