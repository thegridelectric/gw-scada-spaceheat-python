import asyncio
import os
import subprocess
import time
from typing import cast
from typing import Optional

from gwproto import Message

from proactor.message import InternalShutdownMessage
from proactor.proactor_interface import Communicator
from proactor.proactor_interface import MonitoredName
from proactor.proactor_interface import Runnable
from proactor.proactor_interface import ServicesInterface
from proactor.message import KnownNames
from proactor.message import PatExternalWatchdog
from proactor.message import PatExternalWatchdogMessage
from proactor.message import PatInternalWatchdog

class _MonitoredName(MonitoredName):
    last_pat: float = 0.0

class WatchdogManager(Communicator, Runnable):

    RUNNING_AS_SERIVCE_ENV_NAME = "GRIDWORKS_SCADA_RUNNING_AS_SERVICE"

    _watchdog_task: Optional[asyncio.Task] = None
    _seconds_per_pat: float
    _monitored_names: dict[str, _MonitoredName]
    _pat_external_watchdog_process_args: list[str]

    def __init__(
        self,
        seconds_per_pat,
        services: ServicesInterface
    ):
        super().__init__(KnownNames.watchdog_manager.value, services)
        from proactor.proactor_implementation import Proactor
        # noinspection PyProtectedMember
        self.lg = cast(Proactor, services)._logger
        self._seconds_per_pat = seconds_per_pat
        self._monitored_names = dict()
        self._pat_external_watchdog_process_args = []

    def start(self):
        if self._watchdog_task is None:
            if os.getenv(self.RUNNING_AS_SERIVCE_ENV_NAME, "").lower() in ["1", "true"]:
                self._pat_external_watchdog_process_args = [
                    "systemd-notify",
                    f"--pid={os.getpid()}",
                    "WATCHDOG=1",
                ]
            self.lg.lifecycle(f"WatchdogManager: [{' '.join(self._pat_external_watchdog_process_args)}]")
            now = time.time()
            for monitored in self._monitored_names.values():
                monitored.last_pat = now
            self._watchdog_task = asyncio.create_task(self._check_pats(), name="pat_watchdog")

    def stop(self):
        if self._watchdog_task is not None and not self._watchdog_task.done():
            self._watchdog_task.cancel()

    async def join(self):
        if self._watchdog_task is not None:
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass

    def process_message(self, message: Message) -> None:
        self.lg.path("++WatchdogManager.process_message")
        path_dbg = 0
        match message.Payload:
            case PatInternalWatchdog():
                path_dbg |= 0x00000001
                self._pat_internal_watchdog(message.src())
            case PatExternalWatchdog():
                path_dbg |= 0x00000002
                self._pat_external_watchdog()
            case _:
                path_dbg |= 0x00000004
                raise ValueError(f"WatchdogManager does not handle message payloads of type {type(message.Payload)}")
        self.lg.path(f"--WatchdogManager.process_message  0x{path_dbg:08X}")

    def _pat_internal_watchdog(self, name: str):
        if name not in self._monitored_names:
            raise ValueError(f"ERROR. Received interal watchdog pat from unmonitored name: {name}. Monistored names: {list(self._monitored_names.keys())}")
        self._monitored_names[name].last_pat = time.time()

    def add_monitored_name(self, monitored: MonitoredName) -> None:
        if monitored.timeout_seconds <= self._seconds_per_pat / 2:
            raise ValueError(
                f"ERROR. WatchdogManager cannot reliably monitor a timeout of {monitored.timeout_seconds} "
                f"(requested for {monitored.name}) because "
                f"WatchdogManager's _seconds_per_pat (sample rate) is {self._seconds_per_pat}"
            )
        if monitored.name in self._monitored_names:
            raise ValueError(f"ERROR. Name {monitored.name} is already being monitored with {self._monitored_names[monitored.name]}")
        self._monitored_names[monitored.name] = _MonitoredName(monitored.name, monitored.timeout_seconds)

    def _timeout_expired(self) -> Optional[_MonitoredName]:
        # self.lg.path("++timeout_expired")
        path_dbg = 0
        expired: Optional[_MonitoredName] = None
        now = time.time()
        for monitored in self._monitored_names.values():
            path_dbg |= 0x0000001
            required_pat_time = monitored.last_pat + monitored.timeout_seconds
            # self.lg.info(
            #     f"  {monitored.name:50s}  "
            #     f"{monitored.timeout_seconds:4d}  last_pat:{monitored.last_pat:11.1f}  "
            #     f"required_pat_time: {required_pat_time:11.1f}  "
            #     f"now:{now:11.1f}  "
            #     f"remaining: {int(required_pat_time - now):4d}  "
            #     f"required_pat_time < now ? {int(required_pat_time < now)}"
            # )
            if required_pat_time < now:
                path_dbg |= 0x0000002
                expired = monitored
                break
        # self.lg.path(f"--timeout_expired: {int(expired is not None)}  0x{path_dbg:08X}")
        return expired

    async def _check_pats(self) -> None:
        while (expired := self._timeout_expired()) is None:
            self._send(PatExternalWatchdogMessage())
            await asyncio.sleep(self._seconds_per_pat)
        self._send(InternalShutdownMessage(
            Src=self.name,
            Reason=(
                f"Monitored object ({expired.name}) failed to pat internal watchdog.  \n"
                f"  Last pat from {expired.name}: {int(time.time() - expired.last_pat)} seconds ago\n"
                f"  Allowed seconds: {int(expired.timeout_seconds)}"
            )
        ))

    def _pat_external_watchdog(self):
        if self._pat_external_watchdog_process_args:
            subprocess.run(self._pat_external_watchdog_process_args, check=True)
