from actors.primary_scada.primary_scada import PrimaryScada
from actors.sensor.pipe_flow_meter import Pipe_Flow_Meter
from actors.power_meter.power_meter import Power_Meter
from actors.atn.atn import Atn


def main(python_actor_name):
    switcher = {}
    switcher['PrimaryScada'] = PrimaryScada
    switcher['PipeFlowMeter'] = Pipe_Flow_Meter
    switcher['PowerMeter'] = Power_Meter
    switcher['Atn'] = Atn
    func = switcher.get(python_actor_name,
                        lambda x: f"No python implementation for strategy {python_actor_name}")
    return func, switcher.keys()
