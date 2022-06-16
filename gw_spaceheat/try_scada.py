import load_house
from actors.scada import Scada
from data_classes.sh_node import ShNode


def main(input_json_file='input_data/houses.json'):
    load_house.load_all(input_json_file=input_json_file)
    scada_node = ShNode.by_alias["a.s"]
    scada = Scada(scada_node)
    scada.start()
    

if __name__ == "__main__":
    main()
