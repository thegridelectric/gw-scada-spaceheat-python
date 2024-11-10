import asyncio
import time
import uuid
from enum import auto
from typing import Dict, List, Optional

from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, Problems, ServicesInterface
from gwproto import Message
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (ActorClass, ChangeRelayState, FsmReportType,
                           PicoCyclerEvent, PicoCyclerState)
from gwproto.message import Header
from gwproto.messages import PicoMissing
from gwproto.named_types import (ChannelReadings, FsmAtomicReport, FsmEvent,
                                 FsmFullReport, MachineStates)
from result import Ok, Result
from transitions import Machine


class SinglePicoState(GwStrEnum):
    Alive = auto()
    Flatlined = auto()


class PicoCycler(Actor):
    REBOOT_ATTEMPTS = 5
    RELAY_OPEN_S: float = 5
    PICO_REBOOT_S = 60
    STATE_REPORT_S = 300
    ZOMBIE_UPDATE_HR = 1
    _fsm_task: Optional[asyncio.Task] = None
    _stop_requested: bool = False
    actor_by_pico: Dict[str, ShNode]
    pico_actors: List[ShNode]
    pico_states: Dict[str, SinglePicoState]
    pico_relay: ShNode
    trigger_id: Optional[str]
    fsm_reports: List[FsmAtomicReport]
    _stop_requested: bool
    # PicoCyclerState.values()
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
        {"trigger": "PicoMissing", "source": "PicosRebooting", "dest": "RelayOpening"},
    ]

    def __init__(self, name: str, services: ServicesInterface):
        super().__init__(name, services)
        self.layout = self._services.hardware_layout
        self.pico_relay = self.layout.node(H0N.vdc_relay)
        self.pico_actors = [
            node
            for node in self.layout.nodes.values()
            if node.ActorClass in [ActorClass.ApiFlowModule, ActorClass.ApiTankModule]
        ]
        self._stop_requested = False
        self.actor_by_pico = {}
        self.picos = []
        for node in self.pico_actors:
            if node.ActorClass == ActorClass.ApiFlowModule:
                self.actor_by_pico[node.component.gt.HwUid] = node
                self.picos.append(node.component.gt.HwUid)
            if node.ActorClass == ActorClass.ApiTankModule:
                self.actor_by_pico[node.component.gt.PicoAHwUid] = node
                self.picos.append(node.component.gt.HwUid)
                self.actor_by_pico[node.component.gt.PicoAHwUid] = node
        self.pico_states = {pico: SinglePicoState.Alive for pico in self.picos}
        self.primary_scada = self.layout.node(H0N.primary_scada)
        # This counts consecutive failed reboots per pico
        self.reboots_attempted = {pico: 0 for pico in self.picos}
        self.trigger_id = None
        self.fsm_reports = []
        self.last_zombie_report_s = time.time()
        self.machine = Machine(
            model=self,
            states=PicoCycler.states,
            transitions=PicoCycler.transitions,
            initial="PicosLive",
            send_event=True,
        )
        self.state_list = []

    @property
    def flatlined_picos(self) -> List[str]:
        """
        Non-zombie picos that have not been sending messages recently
        """
        non_zombies = [pico for pico in self.picos if pico not in self.zombie_picos]
        flatlined = []
        for pico in non_zombies:
            if self.pico_states[pico] == SinglePicoState.Flatlined:
                flatlined.append(pico)
        return flatlined

    @property
    def zombie_picos(self) -> List[str]:
        """
        Picos that we are supposed to be tracking that have been
        gone for too many consecutive reboots (REBOOT ATTEMPTS)
        """
        zombies = []
        for pico in self.picos:
            if self.reboots_attempted[pico] >= self.REBOOT_ATTEMPTS:
                zombies.append(pico)
        return zombies

    def raise_zombie_pico_warning(self, pico: str) -> None:
        if pico not in self.actor_by_pico:
            raise Exception(
                f"Expect {pico} to be in self.actor_by_pico {self.actor_by_pico}!"
            )
        if self.reboots_attempted[pico] < self.REBOOT_ATTEMPTS:
            raise Exception(
                f"{pico} is not a zombie, should not be in raise_zombie_pico_warning!"
            )
        actor = self.actor_by_pico[pico]
        self._send_to(
            self.primary_scada,
            Problems(warnings=[f"{pico} zombie"]).problem_event(summary=actor.name),
        )


    def process_pico_missing(self, actor: ShNode, payload: PicoMissing) -> None:
        print(f"In process pico missing from {actor.name}")
        if actor not in self.pico_actors:
            return
        pico = payload.PicoHwUid
        self.pico_states[pico] = SinglePicoState.Flatlined

        if self.state == PicoCyclerState.PicosLive:
            orig_state = self.state
            if pico in self.zombie_picos:
                self.services.logger.error(
                    f"{self.name}. Missing {actor} {pico} but "
                    f"ignoring since it has been rebooted {self.reboots_attempted[pico]}"
                    "times without coming back"
                )
                return
            if self.trigger_id is not None:
                raise Exception(
                    f"When state is {self.state}, {self.name} should not have a trigger_id"
                )
            # Machine triggered state change from PicosLivec -> RelayOpening
            self.trigger(PicoCyclerEvent.PicoMissing.value)
            now_ms = int(time.time() * 1000)
            self.report_state(now_ms)
            self.trigger_id = str(uuid.uuid4())
            event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.pico_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=now_ms,
                TriggerId=self.trigger_id,
            )
            self._send_to(self.pico_relay, event)
            self.services.logger.error(
                f"{self.node.handle} sending OpenRelay to {self.pico_relay.name}"
            )

            # increment reboot attempts for all flatlined picos
            for pico in self.pico_states:
                if self.pico_states[pico] == SinglePicoState.Flatlined:
                    self.reboots_attempted[pico] += 1
            self.fsm_reports.append(
                FsmAtomicReport(
                    MachineHandle=self.node.handle,
                    StateEnum=PicoCyclerState.enum_name(),
                    ReportType=FsmReportType.Event,
                    EventType=PicoCyclerEvent.enum_name(),
                    Event=PicoCyclerEvent.PicoMissing,
                    FromState=orig_state,  # PicosLive
                    ToState=self.state,  # RelayOpening
                    UnixTimeMs=event.SendTimeUnixMs,
                    TriggerId=self.trigger_id,
                    Comment=f"powercycle triggered by {actor} {pico}",
                )
            )

    def process_channel_readings(self, actor: ShNode, payload: ChannelReadings) -> None:
        if actor not in self.pico_actors:
            self.services.logger.error(
                f"{self.name} received channel readings from {actor.name}, not one of its pico relays"
            )
            return
        if actor.ActorClass not in [ActorClass.ApiFlowModule, ActorClass.ApiTankModule]:
            raise Exception(
                "Only expect channel readings from ApiFlowModule or ApiTankModule"
                f", not {actor.ActorClass}"
            )

        if actor.ActorClass == ActorClass.ApiFlowModule:
            if payload.ChannelName != actor.name:
                raise Exception(
                    f"[{self.name}] Expect {actor.name} to have channel name {actor.name}!"
                )
            pico = actor.component.gt.HwUid
            if pico not in self.picos:
                raise Exception(f"[{self.name}] {pico} should be in self.picos!")
            self.is_alive(pico)
        elif actor.ActorClass == ActorClass.ApiTankModule:
            if payload.ChannelName in {f"{actor.name}-depth1", f"{actor.name}-depth2"}:
                pico = actor.component.gt.PicoAHwUid
            elif payload.ChannelName in {
                f"{actor.name}-depth3",
                f"{actor.name}-depth4",
            }:
                pico = actor.component.gt.PicoBHwUid
            else:
                raise Exception(
                    f"Do not expect {payload.ChannelName} from TankModule {actor.name}!"
                )
            if pico not in self.picos:
                raise Exception(f"[{self.name}] {pico} should be in self.picos!")
        self.is_alive(pico)

    def is_alive(self, pico: str) -> None:
        if self.pico_states[pico] == SinglePicoState.Flatlined:
            self.pico_states[pico] = SinglePicoState.Alive
            self.reboots_attempted[pico] = 0
            if all(
                self.pico_states[pico] == SinglePicoState.Alive
                for pico in self.zombie_picos
            ):
                self.confirm_rebooted()

    def confirm_rebooted(self) -> None:
        if self.state == PicoCyclerState.PicosRebooting.value:
            # ConfirmRebooted: PicosRebooting -> PicosLive
            self.trigger(PicoCyclerEvent.ConfirmRebooted.value)
            now_ms = int(time.time() * 1000)
            self.report_state(now_ms)
            self.services.logger.error(
                f"[{self.name}] ConfirmRebooted: PicosRebooting -> PicosLive"
            )
            self.fsm_reports.append(
                FsmAtomicReport(
                    MachineHandle=self.node.handle,
                    StateEnum=PicoCyclerState.enum_name(),
                    ReportType=FsmReportType.Event,
                    EventType=PicoCyclerEvent.enum_name(),
                    Event=PicoCyclerEvent.ConfirmRebooted.value,
                    FromState=PicoCyclerState.PicosRebooting.value,
                    ToState=PicoCyclerState.PicosLive.value,
                    UnixTimeMs=now_ms,
                    TriggerId=self.trigger_id,
                )
            )
            if self.state != PicoCyclerState.PicosLive:
                raise Exception(f"State should be PicosLive, got {self.state}")
            # This is the end of the cycle, so send whole report to SCADA and flush trigger_id
            self._send_to(
                self.primary_scada,
                FsmFullReport(
                    FromName=self.name,
                    TriggerId=self.trigger_id,
                    AtomicList=self.fsm_reports,
                ),
            )
            self.fsm_reports = []
            self.trigger_id = None

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
        if relay_report.EventEnum != ChangeRelayState.enum_name():
            raise Exception(
                f"[{self.name}] Expect EventEnum change.relay.state, not {relay_report.EventEnum}"
            )
        if relay_report.Event == ChangeRelayState.OpenRelay:
            self.confirm_opened()
        else:
            self.confirm_closed()

    def process_message(self, message: Message) -> Result[bool, BaseException]:
        src_node = self.layout.node(message.Header.Src)
        if src_node is None:
            self.services.logger.warning(
                f"Ignoring message from {message.Header.Src} - not a known ShNode"
            )
            return
        if isinstance(message.Payload, ChannelReadings):
            self.process_channel_readings(src_node, message.Payload)
            return Ok(True)
        elif isinstance(message.Payload, PicoMissing):
            self.process_pico_missing(src_node, message.Payload)
            return Ok(True)
        elif isinstance(message.Payload, FsmFullReport):
            self.process_fsm_full_report(message.Payload)
            return Ok(True)

    def confirm_opened(self):
        if self.state == PicoCyclerState.RelayOpening.value:
            # ConfirmOpened: RelayOpening -> RelayOpen
            self.trigger(PicoCyclerEvent.ConfirmOpened.value)
            now_ms = int(time.time() * 1000)
            self.fsm_reports.append(
                FsmAtomicReport(
                    MachineHandle=self.node.handle,
                    StateEnum=PicoCyclerState.enum_name(),
                    ReportType=FsmReportType.Event,
                    EventType=PicoCyclerEvent.enum_name(),
                    Event=PicoCyclerEvent.ConfirmOpened.value,
                    FromState=PicoCyclerState.RelayOpening.value,
                    ToState=PicoCyclerState.RelayOpen.value,
                    UnixTimeMs=now_ms,
                    TriggerId=self.trigger_id,
                )
            )
            self.report_state(now_ms)
            asyncio.create_task(self._wait_and_close_relay())

    def confirm_closed(self) -> None:
        # transition from RelayClosing to PicosRebooting
        if self.state == PicoCyclerState.RelayClosing.value:
            # ConfirmClosed: RelayClosing -> PicosRebooting
            self.trigger(PicoCyclerEvent.ConfirmClosed.value)
            now_ms = int(time.time() * 1000)
            self.fsm_reports.append(
                FsmAtomicReport(
                    MachineHandle=self.node.handle,
                    StateEnum=PicoCyclerState.enum_name(),
                    ReportType=FsmReportType.Event,
                    EventType=PicoCyclerEvent.enum_name(),
                    Event=PicoCyclerEvent.ConfirmClosed,
                    FromState=PicoCyclerState.RelayClosing.value,
                    ToState=PicoCyclerState.PicosRebooting.value,
                    UnixTimeMs=now_ms,
                    TriggerId=self.trigger_id,
                )
            )
            self.report_state(now_ms)
            # if not all the picos reboot, powercycle again.
            asyncio.create_task(self._wait_for_rebooting_picos())

    async def _wait_and_close_relay(self) -> None:
        # Wait for RelayOpen_S seconds before closing the relay
        self.services.logger.error(
            f"[{self.name}] Keeping VDC Relay 1 open for {self.RELAY_OPEN_S} seconds"
        )
        await asyncio.sleep(self.RELAY_OPEN_S)
        self.start_closing()

    async def _wait_for_rebooting_picos(self) -> None:
        self.services.logger.error(
            f"[{self.name}, {self.state}] Waiting {self.PICO_REBOOT_S} seconds for picos to come back"
        )
        if self.state != PicoCyclerState.PicosRebooting:
            raise Exception(
                f"Wait and open relay should only happen for PicosRebooting, not {self.state}"
            )
        await asyncio.sleep(self.PICO_REBOOT_S)
        if len(self.flatlined_picos) > 0:
            # PicoMissing:  PicosRebooting -> RelayOpening
            self.trigger(PicoCyclerEvent.PicoMissing.value)
            now_ms = int(time.time() * 1000)
            event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.pico_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.OpenRelay,
                SendTimeUnixMs=now_ms,
                TriggerId=self.trigger_id,
            )
            self._send_to(self.pico_relay, event)
            self.fsm_reports.append(
                FsmAtomicReport(
                    FromHandle=self.node.handle,
                    StateEnum=PicoCyclerState.enum_name(),
                    ReportType=FsmReportType.Event,
                    EventType=PicoCyclerEvent.enum_name(),
                    Event=PicoCyclerEvent.PicoMissing,
                    FromState=PicoCyclerState.PicosRebooting,
                    ToState=PicoCyclerState.RelayOpening,
                    UnixTimeMs=now_ms,
                    TriggerId=self.trigger_id,
                )
            )
            self.report_state(now_ms)
        else:
            self.confirm_rebooted()

    def start_closing(self) -> None:
        # Transition to RelayClosing and send CloseRelayCmd
        if self.state == PicoCyclerState.RelayOpen:
            # StartCLosing: RelayOpen -> RelayClosing
            self.trigger(PicoCyclerEvent.StartClosing)
            now_ms = int(time.time() * 1000)
            event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.pico_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=now_ms,
                TriggerId=self.trigger_id,
            )
            self._send_to(self.pico_relay, event)
            self.fsm_reports.append(
                FsmAtomicReport(
                    MachineHandle=self.node.handle,
                    StateEnum=PicoCyclerState.enum_name(),
                    ReportType=FsmReportType.Event,
                    EventType=PicoCyclerEvent.enum_name(),
                    Event=PicoCyclerEvent.StartClosing,
                    FromState=PicoCyclerState.RelayOpen,
                    ToState=PicoCyclerState.RelayClosing,
                    UnixTimeMs=now_ms,
                    TriggerId=self.trigger_id,
                )
            )
            self.report_state(now_ms)
    
    def start(self) -> None:
        self.services.add_task(
            asyncio.create_task(self.main(), name="ApiFlowModule keepalive")
        )

    def stop(self) -> None:
        """
        IOLoop will take care of shutting down webserver interaction.
        Here we stop periodic reporting task.
        """
        self._stop_requested = True

    async def join(self) -> None:
        """IOLoop will take care of shutting down the associated task."""
        ...

    async def main(self) -> None:
        """
        Responsible for sending synchronous state reports and occasional
        zombie notifications
        """
        while not self._stop_requested:
            sleep_s = max(2, self.STATE_REPORT_S - (time.time() % self.STATE_REPORT_S) - 1)
            await asyncio.sleep(sleep_s)
            self.report_state(int(time.time() * 1000))
            zombie_update_period = self.ZOMBIE_UPDATE_HR * 3600
            last = self.last_zombie_report_s
            next_zombie = last + zombie_update_period - (last % zombie_update_period)
            zombies = []
            for pico in self.zombie_picos:
                zombies.append(f" {pico} [{self.actor_by_pico[pico]}]")
            if time.time() > next_zombie:
                self._send_to(
                    self.primary_scada,
                    Problems(warnings=zombies).problem_event("pico-zombies"),
                )
    
    def report_state(self, now_ms: int) -> None:
        report = MachineStates(
                    MachineHandle=self.node.handle,
                    StateEnum=PicoCyclerState.enum_name(),
                    StateList=[self.state],
                    UnixMsList=[now_ms],
                )
        self.state_list.append(report)
        self._send_to(
                self.primary_scada,
                report
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
