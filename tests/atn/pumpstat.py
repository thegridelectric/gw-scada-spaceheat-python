# FROM TOP_LEVEL DIR: export PYTHONPATH=gw_spaceheat:$PYTHONPATH
import logging
import time
from tests.atn import get_atn
from tests.utils import wait_for

atn = get_atn()

time.sleep(1)

# noinspection PyProtectedMember
logger = atn._logger

def pump_stat_log(s: str, delimit: bool = True):
    if delimit:
        logger.message_summary_logger.info(
            f"~! **************************************************************************************************************************************"
        )
    logger.message_summary_logger.info("~! " + s)

pump_stat_log("STARTING PumpStat")


pump = atn.layout.node("a.tank.out.pump.relay")


logger.message_summary_logger.setLevel(logging.INFO)
logger.setLevel(logging.INFO)


while not atn._link_states[atn.SCADA_MQTT].active():
    logger.info(f"Scada link not read ({atn._link_states[atn.SCADA_MQTT].state.value})")
    time.sleep(10)
i = 0

while True:
    if i % 2 == 0:
        pump_stat_log("Turning on pump")
        atn.turn_on(pump)
        time.sleep(2)
        atn.snap()
        time.sleep(1.5 * 60)
        t = int(time.time())
        pump_stat_log("Turning off pump")
        atn.turn_off(pump)
        time.sleep(13.5 * 60)
    else:
        time.sleep(15 * 60)
    i += 1
