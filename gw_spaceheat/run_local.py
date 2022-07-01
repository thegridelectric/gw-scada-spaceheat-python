import load_house
from command_line_utils import run_nodes_main
from schema.enums.role.role_map import Role
from data_classes.sh_node import ShNode

if __name__ == "__main__":
    load_house.load_all()
    aliases = [
        node.alias
        for node in filter(lambda x: (x.role != Role.ATN and x.has_actor), ShNode.by_alias.values())
    ]
    run_nodes_main(argv=["-n", *aliases])
