# FROM TOP_LEVEL DIR: export PYTHONPATH=gw_spaceheat:$PYTHONPATH
import logging
import time
from tests.atn import get_atn
atn = get_atn()

time.sleep(1)

# noinspection PyProtectedMember
logger = atn._logger

def hatn_log(s: str, delimit: bool = True):
    if delimit:
        logger.message_summary_logger.info(
            f"~! **************************************************************************************************************************************"
        )
    logger.message_summary_logger.info("~! " + s)

hatn_log("STARTING HATN")

boost = atn.layout.node("a.elt1.relay")
pump = atn.layout.node("a.tank.out.pump.relay")
fan = atn.layout.node( "a.tank.out.pump.baseboard1.fan.relay")


logger.message_summary_logger.setLevel(logging.INFO)
logger.setLevel(logging.INFO)

i = 0

while True:
    if i % 48 == 46:
        hatn_log("Turning on boost")
        atn.turn_on(boost)
    elif i % 48 == 47:
        hatn_log("Turning off boost")
        atn.turn_off(boost)
    if i % 2 == 0:
        hatn_log("Turning on pump")
        atn.turn_on(pump)
        time.sleep(2)
        atn.snap()
        time.sleep(3 * 60)
        t = int(time.time())
        hatn_log("Turning off pump")
        atn.turn_off(pump)
        time.sleep(27 * 60)
    else:
        time.sleep(30 * 60)
    i += 1
