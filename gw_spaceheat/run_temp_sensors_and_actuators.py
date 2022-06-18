import load_house
from actors.strategy_switcher import strategy_from_node
from data_classes.sh_node import ShNode
from schema.enums.role.role_map import Role


def main(input_json_file='input_data/houses.json'):
    load_house.load_all(input_json_file=input_json_file)
    all_nodes = list(ShNode.by_alias.values())
    tank_water_temp_sensor_nodes = list(filter(lambda x: (
        x.role == Role.TANK_WATER_TEMP_SENSOR and x.has_actor), all_nodes))
    actuator_nodes = list(filter(lambda x: (
        x.role == Role.BOOLEAN_ACTUATOR and x.has_actor), all_nodes))

    for node in (tank_water_temp_sensor_nodes + actuator_nodes):
        actor_function = strategy_from_node(node)
        if not actor_function:
            raise Exception(f"Expected strategy for {node}!")
        sensor = actor_function(node)
        sensor.start()


if __name__ == "__main__":
    main()
