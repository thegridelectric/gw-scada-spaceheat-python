from actors.primary_scada import PrimaryScada
from actors.pipe_flow_meter import PipeFlowMeter
from actors.tank_water_temp_sensor import TankWaterTempSensor
from actors.power_meter import PowerMeter
from actors.atn import Atn


def main(python_actor_name):
    switcher = {}
    switcher['PrimaryScada'] = PrimaryScada
    switcher['PipeFlowMeter'] = PipeFlowMeter
    switcher['PowerMeter'] = PowerMeter
    switcher['Atn'] = Atn
    switcher['TankWaterTempSensor'] = TankWaterTempSensor
    func = switcher.get(python_actor_name,
                        lambda x: f"No python implementation for strategy {python_actor_name}")
    return func, switcher.keys()


def stickler():
    return None
