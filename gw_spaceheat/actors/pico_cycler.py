import asyncio
import time
import uuid
from enum import auto
from typing import Dict, List, Optional

from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, ServicesInterface
from gwproto import Message
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (ActorClass, ChangeRelayState, FsmEventType,
                           FsmReportType)
from gwproto.message import Header
from gwproto.messages import PicoMissing
from gwproto.named_types import (ChannelReadings, FsmAtomicReport, FsmEvent,
                                 FsmFullReport, SyncedReadings)
from result import Ok, Result
from transitions import Machine


class SinglePicoState(GwStrEnum):
    Alive = auto()
    Flatlined = auto()


class PicoCyclerState(GwStrEnum):
    PicosLive = auto()
    RelayOpening = auto()
    RelayOpen = auto()
    RelayClosing = auto()
    PicosRebooting = auto()


class PicoCyclerEvent(GwStrEnum):
    PicoMissing = auto()
    ConfirmOpened = auto()
    StartClosing = auto()
    ConfirmClosed = auto()
    ConfirmRebooted = auto()


class PicoCycler(Actor):
    RelayOpen_S: float = 5
    _fsm_task: Optional[asyncio.Task] = None
    _stop_requested: bool = False
    picos: Dict[str, ShNode]
    pico_states: Dict[str, SinglePicoState]
    pico_relay: ShNode
    reports_by_trigger: Dict[str, List[FsmAtomicReport]]

    states = [
        "PicosLive",
        "RelayOpening",
        "RelayOpen",
        "RelayClosing",
        "PicosRebooting",
    ]
    transitions = [
        {"trigger": "PicoMissing", "source": "PicosLive", "dest": "RelayOpening"},
        {"trigger": "ConfirmOpened", "source": "RelayOpening", "dest": "RelayOpen"},
        {"trigger": "StartClosing", "source": "RelayOpen", "dest": "RelayClosing"},
        {
            "trigger": "ConfirmClosed",
            "source": "RelayClosing",
            "dest": "PicosRebooting",
        },
        {"trigger": "ConfirmRebooted", "source": "PicosRebooting", "dest": "PicosLive"},
    ]

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self.layout = self._services.hardware_layout
        self.picos = {
            node.name: node
            for node in self.layout.nodes.values()
            if node.ActorClass in [ActorClass.ApiFlowModule, ActorClass.ApiTankModule]
        }
        self.pico_states = {name: SinglePicoState.Alive for name in self.picos.keys()}
        self.pico_relay = self.layout.node(H0N.vdc_relay)
        self.primary_scada = self.layout.node[H0N.primary_scada]
        self.reports_by_trigger = {}
        self.machine = Machine(
            model=self,
            states=PicoCycler.states,
            transitions=PicoCycler.transitions,
            initial="PicosLive",
            send_event=True,
        )

    def some_flatlined(self) -> bool:
        return any(
            state == SinglePicoState.Flatlined for state in self.pico_states.values()
        )

    def process_pico_missing(self, pico: str, payload: PicoMissing) -> None:
        if pico not in self.picos:
            return
        self.pico_states[pico] = SinglePicoState.Flatlined
        if self.state == PicoCyclerState.PicosLive:
            # Machine triggered state change from PicosLivec -> RelayOpening
            self.trigger(PicoCyclerEvent.PicoMissing.value)
            trigger_id = str(uuid.uuid4())
            event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.pico_relay.handle,
                EventType=FsmEventType.ChangeRelayState,
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=trigger_id,
            )
            self._send_to(self.pico_relay, event)
            self.services.logger.error(
                f"{self.node.handle} sending OpenRelay to {self.pico_relay.name}"
            )
            self.reports_by_trigger[trigger_id] = [
                FsmAtomicReport(
                    FromHandle=self.name,
                    AboutFsm="PicoCycler",
                    ReportType=FsmReportType.Event,
                    EventType=FsmEventType.PicoCyclerEvent,
                    Event=PicoCyclerEvent.PicoMissing.value,
                    FromState=PicoCyclerState.PicosLive.value,
                    ToState=PicoCyclerState.RelayOpening.value,
                    UnixTimeMs=event.SendTimeUnixMs,
                    TriggerId=trigger_id,
                )
            ]

    def process_channel_readings(self, pico: str, payload: ChannelReadings) -> None:
        if pico not in self.picos:
            self.services.logger.error(
                f"{self.name} received channel readings from {pico}, not one of its pico relays"
            )
            return
        self.is_alive(pico)

    def process_synced_readings(self, pico: str, payload: ChannelReadings) -> None:
        if pico not in self.picos:
            self.services.logger.error(
                f"{self.name} received channel readings from {pico}, not one of its pico actors"
            )
            return
        self.is_alive(pico)

    def is_alive(self, pico: str) -> None:
        if self.pico_states[pico] == SinglePicoState.Flatlined:
            self.pico_states[pico] = SinglePicoState.Alive
            if all(
                state == SinglePicoState.Alive for state in self.pico_states.values()
            ):
                self.confirm_rebooted()

    def confirm_rebooted(self) -> None:
        if self.state == PicoCyclerState.PicosRebooting.value:
            # ConfirmRebooted: PicosRebooting -> PicosLive
            self.trigger(PicoCyclerEvent.ConfirmRebooted.value)
            if len(self.reports_by_trigger.keys()) != 1:
                raise Exception("Expect a single trigger at a time!")
            trigger_id = list(self.reports_by_trigger.keys())[0]
            self.reports_by_trigger[trigger_id].append(
                FsmAtomicReport(
                    FromHandle=self.node.handle,
                    AbouttFsm="PicoCycler",
                    ReportType=FsmReportType.Event,
                    EventType=FsmEventType.PicoCyclerEvent,
                    Event=PicoCyclerEvent.ConfirmRebooted.value,
                    FromState=PicoCyclerState.PicosRebooting.value,
                    ToState=PicoCyclerState.PicosLive.value,
                    UnixTimeMs=int(time.time() * 1000),
                    TriggerId=trigger_id,
                )
            )
            # This is the end of the cycle, so send whole report to SCADA and flush trigger_id
            self._send_to(
                self.primary_scada,
                FsmFullReport(
                    FromName=self.name,
                    TriggerId=trigger_id,
                    AtomicList=self.reports_by_trigger[trigger_id],
                ),
            )
            self.atomic_list = self.reports_by_trigger[trigger_id]
            self.reports_by_trigger.pop(trigger_id, None)

    def process_fsm_full_report(self, payload: FsmFullReport) -> None:
        if payload.FromName != H0N.vdc_relay:
            raise Exception(
                f"should only get FsmFullReports from VdcRelay, not {payload.FromName}"
            )
        start_time = payload.AtomicList[0].UnixTimeMs
        end_time = payload.AtomicList[-1].UnixTimeMs
        self.services.logger.error(
            f"[{self.name}] Relay1 dispatch took {end_time - start_time} ms"
        )
        relay_report = payload.AtomicList[0]
        if relay_report.EventType != FsmEventType.ChangeRelayState:
            raise Exception(
                f"[{self.name}] Expect EventType ChangeRelayState, not {relay_report.EventType}"
            )
        if relay_report.Event == ChangeRelayState.OpenRelay:
            self.confirm_opened()
        else:
            self.confirm_closed()

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        src = self.layout.node(message.Header.Src, None)
        if isinstance(message.Payload, ChannelReadings):
            self.process_channel_readings(src, message.Payload)
            return Ok(True)
        elif isinstance(message.Payload, SyncedReadings):
            self.process_synced_readings(src, message.Payload)
            return Ok(True)
        elif isinstance(message.Payload, PicoMissing):
            self.process_pico_missing(src, message.Payload)
            return Ok(True)
        elif isinstance(message.Payload, FsmFullReport):
            self.process_fsm_full_report(message.Payload)
            return Ok(True)

    def confirm_opened(self):
        if self.state == PicoCyclerState.RelayOpening.value:
            # ConfirmOpened: RelayOpening -> RelayOpen
            self.trigger(PicoCyclerEvent.ConfirmOpened.value)
            if len(self.reports_by_trigger.keys()) != 1:
                raise Exception("Expect a single trigger at a time!")
            trigger_id = list(self.reports_by_trigger.keys())[0]
            self.reports_by_trigger[trigger_id].append(
                FsmAtomicReport(
                    FromHandle=self.node.handle,
                    AbouttFsm="PicoCycler",
                    ReportType=FsmReportType.Event,
                    EventType=FsmEventType.PicoCyclerEvent,
                    Event=PicoCyclerEvent.ConfirmOpened.value,
                    FromState=PicoCyclerState.RelayOpening.value,
                    ToState=PicoCyclerState.RelayOpen.value,
                    UnixTimeMs=int(time.time() * 1000),
                    TriggerId=trigger_id,
                )
            )
            self._fsm_task = asyncio.create_task(self._wait_and_close_relay())

    def confirm_closed(self) -> None:
        # transition from RelayClosing to PicosRebooting
        if self.state == PicoCyclerState.RelayClosing.value:
            # ConfirmClosed: RelayClosing -> PicosRebooting
            self.trigger(PicoCyclerEvent.ConfirmClosed.value)
            if len(self.reports_by_trigger.keys()) != 1:
                raise Exception("Expect a single trigger at a time!")
            trigger_id = list(self.reports_by_trigger.keys())[0]
            self.reports_by_trigger[trigger_id].append(
                FsmAtomicReport(
                    FromHandle=self.node.handle,
                    AbouttFsm="PicoCycler",
                    ReportType=FsmReportType.Event,
                    EventType=FsmEventType.PicoCyclerEvent,
                    Event=PicoCyclerEvent.ConfirmClosed,
                    FromState=PicoCyclerState.RelayClosing.value,
                    ToState=PicoCyclerState.PicosRebooting.value,
                    UnixTimeMs=int(time.time() * 1000),
                    TriggerId=trigger_id,
                )
            )

    async def _wait_and_close_relay(self) -> None:
        # Wait for RelayOpen_S seconds before closing the relay
        await asyncio.sleep(self.RelayOpen_S)
        self.start_closing()

    def start_closing(self) -> None:
        # Transition to RelayClosing and send CloseRelayCmd
        if self.state == PicoCyclerState.RelayOpen:
            # StartCLosing: RelayOpen -> RelayClosing
            self.trigger(PicoCyclerEvent.StartClosing.value)
            if len(self.reports_by_trigger.keys()) != 1:
                raise Exception("Expect a single trigger at a time!")
            trigger_id = list(self.reports_by_trigger.keys())[0]
            event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.pico_relay.handle,
                EventType=FsmEventType.ChangeRelayState,
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=trigger_id,
            )
            self._send_to(self.pico_relay, event)
            self.reports_by_trigger[trigger_id].append(
                FsmAtomicReport(
                    FromHandle=self.node.handle,
                    AbouttFsm="PicoCycler",
                    ReportType=FsmReportType.Event,
                    EventType=FsmEventType.PicoCyclerEvent,
                    Event=PicoCyclerEvent.StartClosing.value,
                    FromState=PicoCyclerState.RelayOpen.value,
                    ToState=PicoCyclerState.RelayClosing.value,
                    UnixTimeMs=int(time.time() * 1000),
                    TriggerId=trigger_id,
                )
            )

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
