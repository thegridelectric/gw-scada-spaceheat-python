"""Test SimpleSensor actor"""

import load_house
from actors.simple_sensor import SimpleSensor
from config import ScadaSettings
from data_classes.sh_node import ShNode


def test_simple_sensor_value_update():
    settings = ScadaSettings()
    load_house.load_all(settings.world_root_alias)
    thermo0 = SimpleSensor(ShNode.by_alias["a.tank.temp0"], settings=settings)
    try:
        thermo0.start()
        thermo0.terminate_main_loop()
        thermo0.main_thread.join()
        thermo0.update_telemetry_value()
    finally:
        # noinspection PyBroadException
        try:
            thermo0.stop()
        except:
            pass
