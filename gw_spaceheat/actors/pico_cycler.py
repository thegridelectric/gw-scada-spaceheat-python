import asyncio
import time
import uuid
from enum import auto
from typing import Dict, List, Optional, Sequence

from gw.enums import GwStrEnum
from gwproactor import QOS, Actor, MonitoredName, Problems, ServicesInterface
from gwproactor.message import PatInternalWatchdogMessage
from gwproto import Message
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.sh_node import ShNode
from gwproto.enums import (
    ActorClass,
    ChangeRelayState,
    FsmReportType,
    PicoCyclerEvent,
    PicoCyclerState,
)
from gwproto.message import Header
from gwproto.messages import PicoMissing # noqa
from gwproto.named_types import (
    ChannelReadings,
    FsmAtomicReport,
    FsmEvent,
    FsmFullReport,
    MachineStates,
)
from result import Ok, Result
from transitions import Machine

class PicoWarning(ValueError):
    pico_name: str

    def __init__(self, *, msg: str = "", pico_name:str):
        self.pico_name = pico_name
        super().__init__(msg)

    def __str__(self):
        return f"PicoWarning: {self.pico_name}  <{super().__str__()}>"

class ZombiePicoWarning(PicoWarning):

    def __str__(self):
        return f"ZombiePicoWarning: {self.pico_name}  <{super().__str__()}>"

class SinglePicoState(GwStrEnum):
    Alive = auto()
    Flatlined = auto()


class PicoCycler(Actor):
    REBOOT_ATTEMPTS = 3
    RELAY_OPEN_S: float = 5
    PICO_REBOOT_S = 60
    STATE_REPORT_S = 300
    ZOMBIE_UPDATE_HR = 1
    SHAKE_ZOMBIE_HR = 0.5
    _fsm_task: Optional[asyncio.Task] = None
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
        "AllZombies",
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
        {"trigger": "RebootDud", "source": "PicosRebooting", "dest": "AllZombies"},
        {"trigger": "ShakeZombies", "source": "AllZombies", "dest": "RelayOpening"},
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
                self.picos.append(node.component.gt.PicoAHwUid)
                self.actor_by_pico[node.component.gt.PicoBHwUid] = node
                self.picos.append(node.component.gt.PicoBHwUid)
        self.pico_states = {pico: SinglePicoState.Alive for pico in self.picos}
        self.primary_scada = self.layout.node(H0N.primary_scada)
        # This counts consecutive failed reboots per pico
        self.reboots = {pico: 0 for pico in self.picos}
        self.trigger_id = None
        self.fsm_reports = []
        self.last_zombie_problem_report_s = time.time() - 24 * 3600
        self.last_zombie_shake = time.time()
        self.state = "PicosLive"
        self.machine = Machine(
            model=self,
            states=PicoCycler.states,
            transitions=PicoCycler.transitions,
            initial="PicosLive",
            send_event=True,
        )

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
            if self.reboots[pico] >= self.REBOOT_ATTEMPTS:
                zombies.append(pico)
        return zombies

    @property
    def all_zombies(self) -> bool:
        if len(self.zombie_picos) == len(self.picos):
            return True
        return False

    def raise_zombie_pico_warning(self, pico: str) -> None:
        if pico not in self.actor_by_pico:
            raise Exception(
                f"Expect {pico} to be in self.actor_by_pico {self.actor_by_pico}!"
            )
        if self.reboots[pico] < self.REBOOT_ATTEMPTS:
            raise Exception(
                f"{pico} is not a zombie, should not be in raise_zombie_pico_warning!"
            )
        actor = self.actor_by_pico[pico]
        self._send_to(
            self.primary_scada,
            Problems(warnings=[
                ZombiePicoWarning(pico_name=pico)
            ]).problem_event(summary=actor.name),
        )

    def process_pico_missing(self, actor: ShNode, payload: PicoMissing) -> None:
        # ignore messages from other actors unless currently live
        if self.state == PicoCyclerState.PicosLive:
            pico = payload.PicoHwUid
            if pico in self.zombie_picos:
                note = f"Zombie {actor.name} pico {pico} reporting missing"
            else:
                note = f"{actor.name} pico {pico} reporting missing"
            self.services.logger.error(note)
            if actor not in self.pico_actors:
                return

            self.trigger_id = str(uuid.uuid4())
            self.pico_states[pico] = SinglePicoState.Flatlined
            self.pico_missing()

    def pico_missing(self) -> None:
        """
        Called directly when rebooting picos does not bring back all the
        picos, or indirectly when state is PicosLive and we receive a
        PicoMissing message from an actor
        """
        self.trigger_event(PicoCyclerEvent.PicoMissing)

        # increment reboot attempts for all flatlined picos
        for pico in self.pico_states:
            if self.pico_states[pico] == SinglePicoState.Flatlined:
                self.reboots[pico] += 1
                # If this is the first time a pico reaches the zombie threshold,
                # raise that warning
                if self.reboots[pico] == self.REBOOT_ATTEMPTS:
                    self.raise_zombie_pico_warning(pico)
        # Send action on to pico relay
        event = FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.pico_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            SendTimeUnixMs=int(time.time() * 1000),
            TriggerId=self.trigger_id,
        )
        self._send_to(self.pico_relay, event)
        self.services.logger.error(
            f"{self.node.handle} sending OpenRelay to {self.pico_relay.name}"
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

        pico: str | None = None
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
        if pico is None:
            raise ValueError("PICO IS NONE")
        self.is_alive(pico)

    def is_alive(self, pico: str) -> None:
        if self.pico_states[pico] == SinglePicoState.Flatlined:
            self.pico_states[pico] = SinglePicoState.Alive
            self.reboots[pico] = 0
            if all(
                self.pico_states[pico] == SinglePicoState.Alive
                for pico in self.zombie_picos
            ):
                self.confirm_rebooted()

    def confirm_rebooted(self) -> None:
        if self.state == PicoCyclerState.PicosRebooting.value:
            # ConfirmRebooted: PicosRebooting -> PicosLive
            self.trigger_event(PicoCyclerEvent.ConfirmRebooted)
            self.send_fsm_report()

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
        # print(f"++pico_cycler  {message.message_type()}", flush=True)
        path_dbg = 0
        src_node = self.layout.node(message.Header.Src)
        if src_node is not None:
            path_dbg |= 0x00000001
            match message.Payload:
                case ChannelReadings():
                    path_dbg |= 0x00000002
                    self.process_channel_readings(src_node, message.Payload)
                case PicoMissing():
                    path_dbg |= 0x00000004
                    self.process_pico_missing(src_node, message.Payload)
                case FsmFullReport():
                    path_dbg |= 0x00000008
                    self.process_fsm_full_report(message.Payload)
                case _:
                    path_dbg |= 0x00000010
        # print(f"--pico_cycler  path:0x{path_dbg:08X}", flush=True)
        return Ok(True)

    def confirm_opened(self):
        if self.state == PicoCyclerState.RelayOpening.value:
            # ConfirmOpened: RelayOpening -> RelayOpen
            self.trigger_event(PicoCyclerEvent.ConfirmOpened)
            asyncio.create_task(self._wait_and_close_relay())

    def confirm_closed(self) -> None:
        if self.state == PicoCyclerState.RelayClosing.value:
            # ConfirmClosed: RelayClosing -> PicosRebooting
            self.trigger_event(PicoCyclerEvent.ConfirmClosed)
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
        if self.all_zombies:
            self.reboot_dud()
        elif len(self.flatlined_picos) > 0:
            self.pico_missing()
        else:
            self.confirm_rebooted()

    def reboot_dud(self) -> None:
        self.trigger_event(PicoCyclerEvent.RebootDud)
        self.send_fsm_report()

    def shake_zombies(self) -> None:
        self.trigger_id = str(uuid.uuid4())
        self.trigger_event(PicoCyclerEvent.ShakeZombies)
        self.last_zombie_shake = time.time()

    def start_closing(self) -> None:
        # Transition to RelayClosing and send CloseRelayCmd
        if self.state == PicoCyclerState.RelayOpen:
            # StartCLosing: RelayOpen -> RelayClosing
            self.trigger_event(PicoCyclerEvent.StartClosing)
            # Send action on to pico relay
            event = FsmEvent(
                FromHandle=self.node.handle,
                ToHandle=self.pico_relay.handle,
                EventType=ChangeRelayState.enum_name(),
                EventName=ChangeRelayState.CloseRelay,
                SendTimeUnixMs=int(time.time() * 1000),
                TriggerId=self.trigger_id,
            )
            self._send_to(self.pico_relay, event)
            # self.services.logger.error(
            #     f"{self.node.handle} sending Close to {self.pico_relay.name}"
            # )

    def send_fsm_report(self) -> None:
        # This is the end of a triggered cycle, so send  FsmFullReport to SCADA
        # and flush trigger_id and fsm_reports
        self._send_to(
            self.primary_scada,
            FsmFullReport(
                FromName=self.name,
                TriggerId=self.trigger_id,
                AtomicList=self.fsm_reports,
            ),
        )
        self.services.logger.error(
            "Sending report to scada. check "
            f"s._data.recent_fsm_reports['{self.trigger_id}']"
        )
        self.fsm_reports = []
        self.trigger_id = None

    def trigger_event(self, event: PicoCyclerEvent) -> None:
        now_ms = int(time.time() * 1000)
        orig_state = self.state
        self.trigger(event)
        # Add to fsm reports of linked state changes
        self.fsm_reports.append(
            FsmAtomicReport(
                MachineHandle=self.node.handle,
                StateEnum=PicoCyclerState.enum_name(),
                ReportType=FsmReportType.Event,
                EventEnum=PicoCyclerEvent.enum_name(),
                Event=event,
                FromState=orig_state,
                ToState=self.state,
                UnixTimeMs=now_ms,
                TriggerId=self.trigger_id,
            )
        )
        # update the existing states for scada now
        self._send_to(
            self.primary_scada,
            MachineStates(
                MachineHandle=self.node.handle,
                StateEnum=PicoCyclerState.enum_name(),
                StateList=[self.state],
                UnixMsList=[now_ms],
            ),
        )
        self.services.logger.error(
            f"[{self.name}] {event.value}: {orig_state} -> {self.state}"
        )

    def _send_to(self, dst: ShNode, payload) -> None:
        if (
                dst.name == self.services.name or
                self.services.get_communicator(dst.name) is not None
        ):
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
            return self.services.publish_message( # noqa
                self.services.LOCAL_MQTT, # noqa
                message,
                qos=QOS.AtMostOnce,
            )

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

    @property
    def monitored_names(self) -> Sequence[MonitoredName]:
        return [MonitoredName(self.name, self.STATE_REPORT_S * 2.1)]

    async def main(self) -> None:
        """
        Responsible for sending synchronous state reports and occasional
        zombie notifications
        """
        await asyncio.sleep(1)
        trigger_id = str(uuid.uuid4())
        self._send_to(self.pico_relay,
                      FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.pico_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.OpenRelay,
            TriggerId=trigger_id,
            SendTimeUnixMs=int(time.time() * 1000),
                )
        )
        self.services.logger.error(
            f"{self.node.handle}. Initialization: sending OpenRelay to {self.pico_relay.name}"
        )
        await asyncio.sleep(5)
        self._send_to(self.pico_relay,
                      FsmEvent(
            FromHandle=self.node.handle,
            ToHandle=self.pico_relay.handle,
            EventType=ChangeRelayState.enum_name(),
            EventName=ChangeRelayState.CloseRelay,
            TriggerId=trigger_id,
            SendTimeUnixMs=int(time.time() * 1000),
                )
        )
        self.services.logger.error(
            f"{self.node.handle}. Initialization: sending CloseRelay to {self.pico_relay.name}"
        )
        while not self._stop_requested:
            # self.services.logger.error("################# PATTING PICO WATCHDOG")
            self._send(PatInternalWatchdogMessage(src=self.name))
            sleep_s = max(
                1.2, self.STATE_REPORT_S - (time.time() % self.STATE_REPORT_S) - 2
            )
            print(f"[{self.name}] Sleeping for {sleep_s}")
            await asyncio.sleep(sleep_s)
            # report the state
            if sleep_s != 2:
                self._send_to(
                    self.primary_scada,
                    MachineStates(
                        MachineHandle=self.node.handle,
                        StateEnum=PicoCyclerState.enum_name(),
                        StateList=[self.state],
                        UnixMsList=[int(time.time() * 1000)],
                    ),
                )

            # if all picos are zombies, wifi is probably out.
            # power cycle on a semi-regular basis to get them
            # back when wifi is back
            if time.time() - self.last_zombie_shake > self.SHAKE_ZOMBIE_HR * 3600:
                self.shake_zombies()
                print("shaking zombies")
            # report the varios zombie picos as problem events
            zombie_update_period = self.ZOMBIE_UPDATE_HR * 3600
            last = self.last_zombie_problem_report_s
            next_zombie_problem = (
                last + zombie_update_period - (last % zombie_update_period)
            )
            zombies = []
            for pico in self.zombie_picos:
                zombies.append(f" {pico} [{self.actor_by_pico[pico]}]")
            if time.time() > next_zombie_problem:
                self._send_to(
                    self.primary_scada,
                    Problems(warnings=[
                        ZombiePicoWarning(pico_name=zombie_name) for
                        zombie_name in zombies
                    ]).problem_event(summary="pico-zombies"),
                )
                self.last_zombie_problem_report_s = time.time()
