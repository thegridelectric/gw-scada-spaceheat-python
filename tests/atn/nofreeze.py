# This uses the atn stub, but actually represents a first pass at home alone code

import logging
import os
import threading
import time
from typing import List

from actors.utils import responsive_sleep
from data_classes.sh_node import ShNode
from gwproto.enums import TelemetryName

from gw_spaceheat.schema.enums.role import Role
from tests.atn.run import get_atn
from tests.atn.atn import RecentRelayState


class SimpleOrange:
    TANK_TEMP_THRESHOLD_C = 20
    PIPE_TEMP_THRESHOLD_C = 5
    PUMP_ON_MINUTES = 3
    BOOST_ON_MINUTES = 30

    def __init__(self):
        self.atn = get_atn()
        self.relays_initialized: bool = False
        self.strategy_name: str = "SimpleOrange"
        self.actor_main_stopped: bool = True
        self.logger = self.atn._logger
        self.tank_temp_node = self.atn.layout.node("a.tank.temp0")
        self.tank_boost = self.atn.layout.node("a.elt1.relay")

        self.pipe_temp_node = self.atn.layout.node("a.tank.out.far.temp1")
        self.pipe_circulator_pump = self.atn.layout.node("a.tank.out.pump.relay")

        self.logger.message_summary_logger.setLevel(logging.INFO)
        self.logger.setLevel(logging.INFO)

        self.logger.info(
            f"~! **************************************************************************************************************************************"
        )
        self.logger.message_summary_logger.info(f"~! INITIALIZING {self.strategy_name} Atn")
        # self.initialize_relays()
        now = int(time.time())
        self.min_cron_failing: bool = False
        self._last_min_cron_s: int = now - (now % 300)
        self._last_hour_cron_s: int = now - (now % 3600)
        self._last_day_cron_s: int = now - (now % 86400)
        for file in [
            self.atn.settings.minute_cron_file,
            self.atn.settings.hour_cron_file,
            self.atn.settings.day_cron_file,
        ]:
            if not os.path.exists(file):
                # The file does not exist, so create it
                with open(file, "w") as outfile:
                    outfile.write("")
            os.utime(file, (time.time(), time.time()))

        self.main_thread = threading.Thread(target=self.main)

    def local_start(self) -> None:
        self.main_thread.start()
        self.actor_main_stopped = False

    def prepare_for_death(self) -> None:
        self.actor_main_stopped = True

    def local_stop(self) -> None:
        self.main_thread.join()

    ####################
    # Timing and scheduling related
    ####################

    @property
    def next_min_cron_s(self) -> int:
        last_cron_s = self._last_min_cron_s - (self._last_min_cron_s % 60)
        return last_cron_s + 60

    @property
    def next_hour_cron_s(self) -> int:
        last_cron_s = self._last_hour_cron_s - (self._last_hour_cron_s % 3600)
        return last_cron_s + 3600

    @property
    def next_day_cron_s(self) -> int:
        last_day_s = self._last_day_cron_s - (self._last_day_cron_s % 86400)
        return last_day_s + 86400

    def time_for_min_cron(self) -> bool:
        if time.time() > self.next_min_cron_s:
            return True
        return False

    def time_for_hour_cron(self) -> bool:
        if time.time() > self.next_hour_cron_s:
            return True
        return False

    def time_for_day_cron(self) -> bool:
        if time.time() > self.next_day_cron_s:
            return True
        return False

    def cron_every_min_success(self):
        self._last_min_cron_s = int(time.time())
        if self.min_cron_failing is True:
            self.logger.info(f"{self.strategy_name} min cron working again")
        self.min_cron_failing is False
        os.utime(self.atn.settings.minute_cron_file, (time.time(), time.time()))

    def cron_every_hour_success(self):
        self.logger.info(f"{self.strategy_name} cron every hour succeeded")
        self._last_hour_cron_s = int(time.time())
        os.utime(self.atn.settings.hour_cron_file, (time.time(), time.time()))

    def cron_every_day_success(self):
        self._last_day_cron_s = int(time.time())
        self.logger.info(f"{self.strategy_name} cron every day succeeded")
        os.utime(self.atn.settings.day_cron_file, (time.time(), time.time()))

    def cron_every_min(self):
        latest_pipe_reading = self.atn.latest_simple_reading(self.pipe_temp_node)
        if latest_pipe_reading.Unit != TelemetryName.WATER_TEMP_C_TIMES1000:
            raise Exception("expect WATER_TEMP_C_TIMES1000")
        pipe_temp_c = latest_pipe_reading.Value / 1000
        if pipe_temp_c < self.PIPE_TEMP_THRESHOLD_C:
            self.atn.turn_on(self.pipe_circulator_pump)
            self.logger.info(
                f"Pipe temp {pipe_temp_c}C below threshold {self.PIPE_TEMP_THRESHOLD_C}C."
                f" Circulator pump {self.pipe_circulator_pump.alias} on"
            )
        else:
            ps = self.atn.data.relay_state[self.pipe_circulator_pump]
            if ps.State == 1:
                if time.time() - (ps.LastChangeTimeUnixMs / 1000) > 60 * self.PUMP_ON_MINUTES - 5:
                    self.atn.turn_off(self.pipe_circulator_pump)
                    self.logger.info(
                        f"Pump has been on for at least {self.PUMP_ON_MINUTES} minutes "
                        f"and pipe temp {pipe_temp_c}C above threshold {self.PIPE_TEMP_THRESHOLD_C}C. "
                        f"Turning pump {self.pipe_circulator_pump.alias} off "
                    )

        bs = self.atn.data.relay_state[self.tank_boost]
        if bs.State == 1:
            if time.time() - (bs.LastChangeTimeUnixMs / 1000) > 60 * self.BOOST_ON_MINUTES - 5:
                self.atn.turn_off(self.tank_boost)

        self.cron_every_min_success()

    def cron_every_hour(self):
        latest_tank_reading = self.atn.latest_simple_reading(self.tank_temp_node)
        if latest_tank_reading is None:
            return
        if latest_tank_reading.Unit != TelemetryName.WATER_TEMP_C_TIMES1000:
            raise Exception("expect WATER_TEMP_C_TIMES1000")
        tank_temp_c = latest_tank_reading.Value / 1000
        if tank_temp_c < self.TANK_TEMP_THRESHOLD_C:
            self.atn.turn_on(self.tank_boost)

        self.cron_every_hour_success()

    def cron_every_day(self):
        self.cron_every_day_success()

    def initialize_relays(self):
        relay_nodes: List[ShNode] = list(
            filter(lambda x: x.role == Role.BOOLEAN_ACTUATOR, self.atn.layout.nodes.values())
        )
        for node in relay_nodes:
            self.atn.turn_off(node)
            self.atn.data.relay_state[node] = RecentRelayState(
                State=0, LastChangeTimeUnixMs=int(time.time())
            )
            self.logger.info(f"Turning off {node.alias} on initialization")
        self.relays_initialized = True

    def main(self):
        self._main_loop_running = True
        while not self.atn._link_states[self.atn.SCADA_MQTT].active():
            self.logger.warning(
                f"Scada link not ready ({self.atn._link_states[self.atn.SCADA_MQTT].state.value})"
            )
            time.sleep(1)
        self.atn.snap()
        time.sleep(1)
        self.initialize_relays()

        while self._main_loop_running is True:
            if self.time_for_min_cron():
                try:
                    self.cron_every_min()
                except:
                    if self.min_cron_failing is False:
                        self.logger.warning(f"{self.strategy_name} MIN CRON FAILED!!")
                        self.min_cron_failing = True
                    else:
                        if self.time_for_hour_cron():
                            self.logger.warning(f"{self.strategy_name} MIN CRON STILL FAILING!")
            if self.time_for_hour_cron():
                try:
                    self.cron_every_hour()
                except:
                    self.logger.warning(f"{self.strategy_name} hour cron failed")
            if self.time_for_day_cron():
                try:
                    self.cron_every_day()
                except:
                    self.logger.warning(f"{self.strategy_name} day cron failed")

            responsive_sleep(self, 1)


if __name__ == "__main__":
    simple_orange = SimpleOrange()
    simple_orange.local_start()
