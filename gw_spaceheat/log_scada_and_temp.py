import logging

import load_house
from actors.tank_water_temp_sensor import TankWaterTempSensor
from actors.scada import Scada
from data_classes.sh_node import ShNode

logging.basicConfig(level="DEBUG")

load_house.load_all(input_json_file="input_data/houses.json")
node = ShNode.by_alias["a.tank.temp0"]
temp0 = TankWaterTempSensor(node, logging_on=True)

temp0.start()

node = ShNode.by_alias["a.s"]
scada = Scada(node, logging_on=True)

scada.start()
