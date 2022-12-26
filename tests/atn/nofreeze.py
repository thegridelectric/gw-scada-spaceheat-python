# FROM TOP_LEVEL DIR: export PYTHONPATH=gw_spaceheat:$PYTHONPATH
import logging
import time
from gwproto.messages import TelemetrySnapshotSpaceheat
from gwproto.enums import TelemetryName
from tests.atn import get_atn
from tests.utils import wait_for

TEMP_THRESHOLD_C = 10

atn = get_atn()

time.sleep(1)
boost = atn.layout.node("a.elt1.relay")
atn.turn_off(boost)

# noinspection PyProtectedMember
logger = atn._logger

def no_freeze_log(s: str, delimit: bool = True):
    if delimit:
        logger.message_summary_logger.info(
            f"~! **************************************************************************************************************************************"
        )
    logger.message_summary_logger.info("~! " + s)

no_freeze_log("STARTING NoFreeze")


logger.message_summary_logger.setLevel(logging.INFO)
logger.setLevel(logging.INFO)

while not atn._link_states[atn.SCADA_MQTT].active():
    logger.info(f"Scada link not read ({atn._link_states[atn.SCADA_MQTT].state.value})")
    time.sleep(10)
i = 0



while True:
    atn.snap()
    time.sleep(1)
    snap = atn.data.latest_snapshot.Snapshot
    idx = snap.AboutNodeAliasList.index('a.tank.temp0')
    
    units = snap.TelemetryNameList[idx]
    if not units == TelemetryName.WATER_TEMP_C_TIMES1000:
        raise Exception(f"Unexpected units for tank temp {units}")
    
    tank_temp_c = snap.ValueList[idx] / 1000

    if tank_temp_c < TEMP_THRESHOLD_C :
        no_freeze_log(f"a.tank.temp0 is {tank_temp_c} C. Turning on boost for an hour")
        atn.turn_on(boost)
        time.sleep(3600)
        atn.turn_off(boost)
    else:
        time.sleep(60)
    

