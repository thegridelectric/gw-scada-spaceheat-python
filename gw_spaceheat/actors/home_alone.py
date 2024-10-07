import asyncio
import dataclasses
import time
from dataclasses import dataclass
from typing import Optional
from typing import Sequence

from gwproto import Message
from gwproto.enums import TelemetryName
from gwproto.types import SnapshotSpaceheat
from result import Err
from result import Ok
from result import Result

from actors.scada_interface import ScadaInterface
from gwproto.data_classes.sh_node import ShNode
from gwproactor import MonitoredName
from gwproactor.message import PatInternalWatchdogMessage
from gwproactor import Actor


@dataclass
class RecentRelayState:
    state: Optional[int] = None
    last_change_time_unix_ms: Optional[int] = None


@dataclass
class HomeAloneData:
    latest_snapshot: Optional[SnapshotSpaceheat] = None
    relay_state: dict[str, RecentRelayState] = dataclasses.field(default_factory=dict)

    def latest_simple_reading(self, name: str) -> Optional[int]:
        """Provides the latest reported Telemetry value as reported in a snapshot
        message from the Scada, for a simple sensor.

        Args:
            name (str): The name of a Spaceheat Node associated to a simple sensor.

        Returns:
            Optional[int]: Returns None if no value has been reported.
            This will happen for example if the node is not associated to
            a simple sensor.
        """
        # noinspection PyBroadException
        try:
            # self.latest_snapshot might be None or 'name' might not be present
            idx = self.latest_snapshot.Snapshot.AboutNodeAliasList.index(name)
            return self.latest_snapshot.Snapshot.ValueList[idx]
        except:
            return None

# TODO: HomeAlone should be able to handle flexible units; e.g. not require
#       thermo to report in Celsius.


@dataclass
class _LoopTimes:
    last_minute_s: int = 0
    last_hour_s: int = 0
    last_day_s: int = 0

    def minute_passed(self, now) -> bool:
        return now >= self.last_minute_s + 60

    def hour_passed(self, now) -> bool:
        return now >= self.last_hour_s + 3600

    def day_passed(self, now) -> bool:
        return now >= self.last_day_s + (24 * 3600)

    def update_last_minute(self, now):
        self.last_minute_s = int(now)

    def update_last_hour(self, now):
        self.last_hour_s = int(now)

    def update_last_day(self, now):
        self.last_day_s = int(now)


class HomeAlone(Actor):
    LOOP_SLEEP_SECONDS: float = 60
    TANK_TEMP_THRESHOLD_C: float = 20
    PIPE_TEMP_THRESHOLD_C: float = 15
    PUMP_ON_MINUTES: int = 3
    BOOST_ON_MINUTES: int = 30
    TANK_THERMO_NAME: str = "a.tank.temp0"
    TANK_BOOST_NAME: str = "a.elt1.relay"
    PIPE_THERMO_NAME: str = "a.tank.out.far.temp1"
    PUMP_NAME: str = "a.tank.out.pump.relay"

    _monitor_task: Optional[asyncio.Task] = None
    _stop_requested: bool = False
    _nodes: dict[str, ShNode]
    _data: HomeAloneData
    _loop_times: _LoopTimes

    def __init__(self, name: str, services: ScadaInterface):
        super().__init__(name, services)
        self._nodes = {
            name: self.services.hardware_layout.node(name) for name in [
                self.TANK_THERMO_NAME,
                self.TANK_BOOST_NAME,
                self.PIPE_THERMO_NAME,
                self.PUMP_NAME,
            ]
        }
        self._data = HomeAloneData(relay_state={relay_name: RecentRelayState() for relay_name in self._nodes})
        self._loop_times = _LoopTimes()

    @property
    def tank_thermo(self) -> ShNode:
        return self._nodes[self.TANK_THERMO_NAME]

    @property
    def tank_boost(self) -> ShNode:
        return self._nodes[self.TANK_BOOST_NAME]

    @property
    def pipe_thermo(self) -> ShNode:
        return self._nodes[self.PIPE_THERMO_NAME]

    @property
    def pump(self) -> ShNode:
        return self._nodes[self.PUMP_NAME]

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if isinstance(message.Payload, SnapshotSpaceheat):
            return self._process_snapshot(message.Payload)
        return Err(ValueError(
            f"Error. {self.__class__.__name__} "
            f"{self.name} receieved unexpected message: {message.Header}")
        )

    def _process_snapshot(self, snapshot: SnapshotSpaceheat) -> Result[bool, BaseException]:
        self._data.latest_snapshot = snapshot
        for i, about_alias in enumerate(snapshot.Snapshot.AboutNodeAliasList):
            if (
                about_alias in self._nodes
                and snapshot.Snapshot.TelemetryNameList[i] == TelemetryName.RelayState
            ):
                relay_state = self._data.relay_state[about_alias]
                if relay_state.state != snapshot.Snapshot.ValueList[i]:
                    relay_state.state = snapshot.Snapshot.ValueList[i]
                    relay_state.last_change_time_unix_ms = snapshot.Snapshot.ReportTimeUnixMs
        return Ok()

    def start(self):
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor(), name="HomeAlone.monitor")

    def stop(self):
        self._stop_requested = True
        if self._monitor_task is not None and not self._monitor_task.done():
            self._monitor_task.cancel()

    async def join(self):
        if self._monitor_task is not None:
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor(self):
        while not self._stop_requested:
            now = time.time()
            self._send(PatInternalWatchdogMessage(src=self.name))
            if self._loop_times.minute_passed(now):
                self.per_minute_job(now)
                self._loop_times.update_last_minute(now)
            if self._loop_times.hour_passed(now):
                self.per_hour_job()
                self._loop_times.update_last_hour(now)
            if self._loop_times.day_passed(now):
                self.per_day_job()
                self._loop_times.update_last_day(now)
            await asyncio.sleep(self.LOOP_SLEEP_SECONDS)

    def _set_relay(self, relay_name: str, state: bool):
        ...
        # self._send(GtDispatchBooleanLocalMessage(src=self.name, dst=relay_name, relay_state=int(state)))

    def per_minute_job(self, now: float) -> None:
        latest_pipe_reading = self._data.latest_simple_reading(self.PIPE_THERMO_NAME)
        if latest_pipe_reading is not None:
            pipe_temp_c = latest_pipe_reading / 1000
            if pipe_temp_c < self.PIPE_TEMP_THRESHOLD_C:
                self._set_relay(self.PUMP_NAME, True)
                self.services.logger.info(
                    f"Pipe temp {pipe_temp_c}C below threshold {self.PIPE_TEMP_THRESHOLD_C}C."
                    f" Circulator pump {self.PUMP_NAME} on"
                )
            else:
                pipe_state = self._data.relay_state[self.PUMP_NAME]
                if pipe_state.state == 1:
                    if now - (pipe_state.last_change_time_unix_ms / 1000) > 60 * self.PUMP_ON_MINUTES - 5:
                        self._set_relay(self.PUMP_NAME, False)
                        self.services.logger.info(
                            f"Pump has been on for at least {self.PUMP_ON_MINUTES} minutes "
                            f"and pipe temp {pipe_temp_c}C above threshold {self.PIPE_TEMP_THRESHOLD_C}C. "
                            f"Turning pump {self.PUMP_NAME} off "
                        )

        boost_state = self._data.relay_state[self.TANK_BOOST_NAME]
        if boost_state.state == 1:
            if now - (boost_state.last_change_time_unix_ms / 1000) > 60 * self.BOOST_ON_MINUTES - 5:
                self._set_relay(self.TANK_BOOST_NAME, False)

    def per_hour_job(self) -> None:
        latest_tank_reading = self._data.latest_simple_reading(self.TANK_THERMO_NAME)
        if latest_tank_reading is None:
            return
        if (latest_tank_reading / 1000) < self.TANK_TEMP_THRESHOLD_C:
            self._set_relay(self.TANK_BOOST_NAME, True)

    def per_day_job(self) -> None:
        ...

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.LOOP_SLEEP_SECONDS * 2)]
