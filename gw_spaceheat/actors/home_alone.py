import asyncio
from datetime import datetime
from abc import ABC, abstractmethod
import pytz
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from gwproactor import QOS, Actor, MonitoredName, ServicesInterface
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (ChangeRelayState, FsmEventType, FsmReportType,
                           RelayClosedOrOpen, StoreFlowDirection,
                           TelemetryName)
from gwproto.message import Header
from gwproto.named_types import FsmAtomicReport, FsmEvent, FsmFullReport
from result import Err, Ok, Result


@dataclass
class _LoopTimes:
    last_minute_s: int = 0
    last_hour_s: int = 0
    last_day_s: int = 0

    def minute_passed(self, now) -> bool:
        return now >= self.last_minute_s + 10

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
    LOOP_SLEEP_SECONDS: float = 10
    _monitor_task: Optional[asyncio.Task] = None
    _stop_requested: bool = False
    vdc_relay_state: RelayClosedOrOpen
    vdc_relay: ShNode
    reports_by_trigger: Dict[str, List[FsmAtomicReport]]

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self.layout = self._services.hardware_layout
        self._loop_times = _LoopTimes()
        self.vdc_relay_state = RelayClosedOrOpen.RelayClosed
        self.vdc_relay = self.layout.node(H0N.vdc_relay)
        self.reports_by_trigger: Dict[str, List[FsmAtomicReport]] = {}

    @property
    def primary_scada(self) -> ShNode:
        return self.layout.nodes[H0N.primary_scada]
    
    def start(self):
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(
                self._monitor(), name="HomeAlone.monitor"
            )

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

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        if isinstance(message.Payload, FsmFullReport):
            return self._process_fsm_full_report(message.Payload)
        return Err(
            ValueError(
                f"Error. {self.__class__.__name__} "
                f"{self.name} receieved unexpected message: {message.Header}"
            )
        )

    def _process_fsm_full_report(
        self, payload: FsmFullReport
    ) -> Result[bool, BaseException]:
        # This should be a relay reporting back on a dispatch
        start_time = payload.AtomicList[0].UnixTimeMs / 1000
        end_time = payload.AtomicList[-1].UnixTimeMs / 1000
        self.services.logger.error(f"Took {round(end_time - start_time, 3)} seconds")
        # for a in payload.AtomicList:
        #     ft = datetime.fromtimestamp(a.UnixTimeMs / 1000).strftime("%H:%M:%S.%f")[:-3]
        #     if a.ReportType == FsmReportType.Action:
        #         self.services.logger.error(
        #             f"[{ft}] ACTION \t{a.FromHandle} \t \t [Fsm {a.AboutFsm}]: \t \t \t{a.Action}"
        #         )
        #     else:
        #         self.services.logger.error(
        #             f"[{ft}] EVENT  \t{a.FromHandle} \t \t [Fsm {a.AboutFsm}] {a.Event}: \tfrom {a.FromState} to {a.ToState}"
        #         )
        self._send_to(self.primary_scada, payload)

    def is_boss_of(self, relay: ShNode) -> bool:
        immediate_boss = ".".join(relay.Handle.split(".")[:-1])
        if immediate_boss != self.node.handle:
            return False
        return True

    def change_vdc(self, cmd: ChangeRelayState):
        if not self.is_boss_of(self.vdc_relay):
            raise Exception("Should not try to change vdc when not its boss")
        trigger_id = str(uuid.uuid4())
        self.reports_by_trigger[trigger_id] = []
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.vdc_relay.handle,
            EventType=FsmEventType.ChangeRelayState,
            EventName=cmd,
            SendTimeUnixMs=int(time.time() * 1000),
            TriggerId=trigger_id,
        )
        self._send_to(self.vdc_relay, event)
        self.services.logger.error(f"Sending {cmd} to {self.vdc_relay.name}")

    async def _monitor(self):
        while not self._stop_requested:
            now = time.time()
            print("patting watchdog")
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

    def per_minute_job(self, now: float) -> None:
        if self.vdc_relay_state == RelayClosedOrOpen.RelayOpen:
            target_state = RelayClosedOrOpen.RelayClosed
        else:
            target_state = RelayClosedOrOpen.RelayOpen
        self.services.logger.error(f"Running per minute job: targetting {target_state}")
        self.change_vdc(target_state)
        
    def per_hour_job(self) -> None:
        ...

    def per_day_job(self) -> None:
        ...

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.LOOP_SLEEP_SECONDS * 2)]

    def _send_to(self, dst: ShNode, payload) -> None:
        if dst.name in set(self.services._communicators.keys()) | {self.services.name}:
            self._send(
                Message(
                    header=Header(
                        Src=self.name,
                        Dst=dst.name,
                        MessageType=payload.TypeName,
                    ),
                    Payload=payload,
                )
            )
        else:
            # Otherwise send via local mqtt
            message = Message(Src=self.name, Dst=dst.name, Payload=payload)
            return self.services._links.publish_message(
                self.services.LOCAL_MQTT, message, qos=QOS.AtMostOnce
            )

# class NsmBase(ABC):
#     ONPEAK_START_1_HR = 7
#     ONPEAK_STOP_1_HR = 12
#     ONPEAK_START_2_HR = 16
#     ONPEAK_STOP_2_HR = 20
#     todays_seconds: int
#     prev_seconds: int

#     def __init__(self):
#         self.todays_seconds: int = 0
#         self.prev_seconds: int = 0
#         self.krida_relay_pin = None

#         self.check_relay_consistency()
#         self.update_time()
#         self.update_time()


# def is_weekend(tz: str = 'America/New_York') -> bool:
#     # Get the current date and time in the specified time zone
#     timezone = pytz.timezone(tz)
#     now = datetime.now(timezone)
#     # Check if it's Saturday (5) or Sunday (6)
#     if now.weekday() in [5, 6]:
#         return True
#     else:
#         return False

