from data_classes.sh_node import ShNode
import actors.strategy_switcher as strategy_switcher
import load_dev_house
load_dev_house.load_all()


actor_nodes = list(filter(lambda x: x.python_actor_name is not None, ShNode.by_alias.values()))

node = actor_nodes[0]

node = actor_nodes[1]
(actor_function, keys) = strategy_switcher.main(node.python_actor_name)

actor_function(node=node)