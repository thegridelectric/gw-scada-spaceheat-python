# FROM TOP_LEVEL DIR: export PYTHONPATH=gw_spaceheat:$PYTHONPATH
import logging
import time
import pendulum
from tests.atn import get_atn
atn = get_atn()

atn.snap()

boost = atn.layout.node("a.elt1.relay")
pump = atn.layout.node("a.tank.out.pump.relay")
fan = atn.layout.node( "a.tank.out.pump.baseboard1.fan.relay")

atn.turn_on(boost)


atn._logger.message_summary_logger.setLevel(logging.INFO)
atn._logger.setLevel(logging.INFO)

i = 0

while True:
    t = int(time.time())
    d = pendulum.from_timestamp(t)
    if i % 48 == 46:
        print(f"{d} Turning on boost")
        atn.turn_on(boost)
    elif i % 48 == 47:
        print(f"{d} Turning off boost")
        atn.turn_off(boost)
    if i % 2 == 0:        
        print(f"{d} Turning on pump")
        atn.turn_on(pump)
        time.sleep(3 * 60)
        t = int(time.time())
        d = pendulum.from_timestamp(t)
        print(f"{d} Turning off pump")
        atn.turn_off(pump)
        time.sleep(27 * 60)
    else:
        time.sleep(30 * 60)
    i += 1
