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
from gwproto.enums import StoreFlowRelay, ChangeStoreFlowRelay
from gwproto.message import Header
from gwproto.named_types import FsmAtomicReport, FsmEvent, FsmFullReport
from result import Err, Ok, Result


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
    _monitor_task: Optional[asyncio.Task] = None
    _stop_requested: bool = False
    charge_discharge_relay_state: StoreFlowRelay
    charge_discharge_relay: ShNode
    reports_by_trigger: Dict[str, List[FsmAtomicReport]]

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self.layout = self._services.hardware_layout
        self._loop_times = _LoopTimes()
        self.charge_discharge_relay_state = StoreFlowRelay.DischargingStore
        self.charge_discharge_relay = self.layout.node(H0N.store_charge_discharge_relay)
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
        self.services.logger.error(f"######################## Took {round(end_time - start_time, 3)} seconds ########")
        self.fsm_report = payload
        #TODO: update relay state
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

    def change_charge_discharge(self, cmd: ChangeStoreFlowRelay):
        if not self.is_boss_of(self.charge_discharge_relay):
            self.services.logger.error(f"{self.name} Should not try to change  {self.charge_discharge_relay.handle} when not its boss")
            return
        trigger_id = str(uuid.uuid4())
        self.reports_by_trigger[trigger_id] = []
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.charge_discharge_relay.handle,
            EventType=ChangeStoreFlowRelay.enum_name(),
            EventName=cmd.value,
            SendTimeUnixMs=int(time.time() * 1000),
            TriggerId=trigger_id,
        )
        self._send_to(self.charge_discharge_relay, event)
        self.services.logger.error(f"Sending {cmd} to {self.charge_discharge_relay.name}")

    async def _monitor(self):
        while not self._stop_requested:
            now = time.time()
            # self.services.logger.warning("patting homealone watchdog")
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
        ...
        # if self.charge_discharge_relay_state == StoreFlowRelay.DischargingStore:
        #     cmd = ChangeStoreFlowRelay.ChargeStore
        #     self.charge_discharge_relay_state = StoreFlowRelay.ChargingStore
        # else:
        #     cmd = ChangeStoreFlowRelay.DischargeStore
        #     self.charge_discharge_relay_state = StoreFlowRelay.DischargingStore
        # self.services.logger.error(f"Running per minute job: running {cmd}")
        # self.change_charge_discharge(cmd)
        
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
