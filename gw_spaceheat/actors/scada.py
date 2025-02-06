"""Scada implementation"""
import os
import asyncio
import enum
import uuid
import threading
import time
from typing import Any, List, Optional, cast

import dotenv
from transitions import Machine
from gwproto.message import Header
from gwproactor.external_watchdog import SystemDWatchdogCommandBuilder
from gwproactor.links import LinkManagerTransition
from gwproactor.links.link_settings import LinkSettings
from gwproto import create_message_model

from gwproto.enums import ActorClass

from actors.power_meter import PowerMeter
from data_classes.house_0_layout import House0Layout
from gwproto.messages import FsmFullReport
from gwproto.messages import EventBase
from gwproto.message import Message
from gwproto.messages import PowerWatts
from gwproto.messages import SendSnap

from gwproto.named_types import (
    AnalogDispatch, ChannelReadings, MachineStates, SingleReading, SyncedReadings,
)

from gwproto.messages import ReportEvent
from gwproto import MQTTCodec
from result import Ok
from result import Result

from gwproactor import ActorInterface
from actors.scada_data import ScadaData
from actors.scada_interface import ScadaInterface
from actors.config import ScadaSettings
from gwproto.data_classes.sh_node import ShNode
from gwproactor import QOS

from gwproactor.links import Transition
from gwproactor.message import MQTTReceiptPayload
from gwproactor.persister import TimedRollingFilePersister
from gwproactor.proactor_implementation import Proactor

from data_classes.house_0_names import H0N
from enums import MainAutoState, StratBossState, StratBossEvent, TopState
from named_types import (
    AdminDispatch, AdminKeepAlive, AdminReleaseControl, AllyGivesUp, ChannelFlatlined,
    DispatchContractGoDormant, DispatchContractGoLive, EnergyInstruction, GameOn, GoDormant,
    LayoutLite, NewCommandTree, RemainingElec, RemainingElecEvent, ScadaParams, SendLayout,
    SingleMachineState, SuitUp, WakeUp, HackOilOn, HackOilOff, StratBossTrigger
)

ScadaMessageDecoder = create_message_model(
    "ScadaMessageDecoder",
    [
        "named_types",
        "gwproto.messages",
        "gwproactor.message",
        "actors.message",
    ],
)


class GridworksMQTTCodec(MQTTCodec):
    exp_src: str
    exp_dst: str = H0N.primary_scada

    def __init__(self, hardware_layout: House0Layout):
        self.exp_src = hardware_layout.atn_g_node_alias
        super().__init__(ScadaMessageDecoder)

    def validate_source_and_destination(self, src: str, dst: str) -> None:
        if src != self.exp_src or dst != self.exp_dst:
            raise ValueError(
                "ERROR validating src and/or dst\n"
                f"  exp: {self.exp_src} -> {self.exp_dst}\n"
                f"  got: {src} -> {dst}"
            )


class LocalMQTTCodec(MQTTCodec):
    exp_srcs: set[str]
    exp_dst: str

    def __init__(self, *, primary_scada: bool, remote_node_names: set[str]):
        self.primary_scada = primary_scada
        self.exp_srcs = remote_node_names
        if self.primary_scada:
            self.exp_srcs.add(H0N.secondary_scada)
            self.exp_dst = H0N.primary_scada
        else:
            self.exp_srcs.add(H0N.primary_scada)
            self.exp_dst = H0N.secondary_scada

        super().__init__(ScadaMessageDecoder)

    def validate_source_and_destination(self, src: str, dst: str) -> None:
        ## Black Magic 🪄
        ##   The message from scada2 contain the *spaceheat name* as
        ##   src, *not* the gnode name, in particular because they might come
        ##   from individual nodes that don't have a gnode.
        ##   Since spaceheat names now contain '-', the encoding/decoding by
        ##   MQTTCodec (done for Rabbit) is not what we we want: "-" ends up as
        ##   "." So we have undo that in this particular case.
        src = src.replace(".", "-")
        ## End Black Magic 🪄

        if dst != self.exp_dst or src not in self.exp_srcs:
            raise ValueError(
                "ERROR validating src and/or dst\n"
                f"  exp: one of {self.exp_srcs} -> {self.exp_dst}\n"
                f"  got: {src} -> {dst}"
            )


class AdminCodec(MQTTCodec):
    scada_gnode: str

    def __init__(self, scada_gnode: str):
        self.scada_gnode = scada_gnode

        super().__init__(ScadaMessageDecoder)

    def validate_source_and_destination(self, src: str, dst: str) -> None:
        if dst != self.scada_gnode or src != H0N.admin:
            raise ValueError(
                "ERROR validating src and/or dst\n"
                f"  exp: one of {H0N.admin} -> {self.scada_gnode}\n"
                f"  got: {src} -> {dst}"
            )


class ScadaCmdDiagnostic(enum.Enum):
    SUCCESS = "Success"
    PAYLOAD_NOT_IMPLEMENTED = "PayloadNotImplemented"
    BAD_FROM_NODE = "BadFromNode"
    DISPATCH_NODE_NOT_RELAY = "DispatchNodeNotRelay"
    UNKNOWN_DISPATCH_NODE = "UnknownDispatchNode"
    IGNORING_HOMEALONE_DISPATCH = "IgnoringHomealoneDispatch"
    IGNORING_ATN_DISPATCH = "IgnoringAtnDispatch"


class Scada(ScadaInterface, Proactor):
    ASYNC_POWER_REPORT_THRESHOLD = 0.05
    DEFAULT_ACTORS_MODULE = "actors"
    ATN_MQTT = "gridworks"
    LOCAL_MQTT = "local"
    ADMIN_MQTT = "admin"

    _data: ScadaData
    _last_report_second: int
    _last_snap_s: int
    _channels_reported: bool
    _admin_timeout_task: Optional[asyncio.Task] = None

    top_states = ["Auto", "Admin"]
    top_transitions = [
        {"trigger": "AdminWakesUp", "source": "Auto", "dest": "Admin"},
        {"trigger": "AdminTimesOut", "source": "Admin", "dest": "Auto"},
        {"trigger": "AdminReleasesControl", "source": "Admin", "dest": "Auto"},
    ]

    main_auto_states = ["Atn", "HomeAlone", "Dormant"]
    main_auto_transitions = [
        {"trigger": "AtnLinkDead", "source": "Atn", "dest": "HomeAlone"},
        {"trigger": "AtnWantsControl", "source": "HomeAlone", "dest": "Atn"},
        {"trigger": "AutoGoesDormant", "source": "Atn", "dest": "Dormant"},
        {"trigger": "AutoGoesDormant", "source": "HomeAlone", "dest": "Dormant"},
        {"trigger": "AutoWakesUp", "source": "Dormant", "dest": "HomeAlone"},
        {"trigger": "AtnReleasesControl", "source": "Atn", "dest": "HomeAlone"},
        {"trigger": "AllyGivesUp", "source": "Atn", "dest": "HomeAlone"},
    ]

    def __init__(
        self,
        name: str,
        settings: ScadaSettings,
        hardware_layout: House0Layout,
        actor_nodes: Optional[List[ShNode]] = None,
    ):
        if not isinstance(hardware_layout, House0Layout):
            raise Exception("Make sure to pass Hosue0Layout object as hardware_layout!")
        self.is_simulated = False
        self._layout: House0Layout = hardware_layout
        self._data = ScadaData(settings, hardware_layout)
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        scada2_gnode_name = (
            f"{hardware_layout.scada_g_node_alias}.{H0N.secondary_scada}"
        )
        remote_actor_node_names = {
            node.name
            for node in self._layout.nodes.values()
            if self._layout.parent_node(node) != self._node
            and node != self._node
            and node.has_actor
        } | {scada2_gnode_name.replace(".", "-")}
        self._links.add_mqtt_link(
            LinkSettings(
                client_name=self.LOCAL_MQTT,
                gnode_name=scada2_gnode_name,
                spaceheat_name=H0N.secondary_scada,
                mqtt=self.settings.local_mqtt,
                codec=LocalMQTTCodec(
                    primary_scada=True, remote_node_names=remote_actor_node_names
                ),
                downstream=True,
            )
        )
        self._links.add_mqtt_link(
            LinkSettings(
                client_name=self.ATN_MQTT,
                gnode_name=self._layout.atn_g_node_alias,
                spaceheat_name=H0N.atn,
                mqtt=self.settings.gridworks_mqtt,
                codec=GridworksMQTTCodec(self._layout),
                upstream=True,
            )
        )
        if self.settings.admin.enabled:
            self._links.add_mqtt_link(
                LinkSettings(
                    client_name=self.ADMIN_MQTT,
                    gnode_name=self.settings.admin.name,
                    spaceheat_name=self.settings.admin.name,
                    subscription_name=self.publication_name,
                    mqtt=self.settings.admin,
                    codec=AdminCodec(self.publication_name),
                ),
            )
        self._links.log_subscriptions("construction")
        now = int(time.time())
        self._channels_reported = False
        self._last_report_second = int(now - (now % self.settings.seconds_per_report))
        self._last_snap_s = int(now - (now % self.settings.seconds_per_snapshot))
        self.pending_dispatch: Optional[AnalogDispatch] = None
        self.logger.add_category_logger(
            PowerMeter.POWER_METER_LOGGER_NAME,
            level=settings.power_meter_logging_level,
        )
        self.set_home_alone_command_tree()
        if actor_nodes is not None:
            for actor_node in actor_nodes:
                self.add_communicator(
                    ActorInterface.load(
                        actor_node.Name,
                        str(actor_node.actor_class),
                        self,
                        self.DEFAULT_ACTORS_MODULE,
                    )
                )
        self.top_state: TopState = TopState.Auto
        self.top_machine = Machine(
            model=self,
            states=Scada.top_states,
            transitions=Scada.top_transitions,
            initial=TopState.Auto,
            send_event=False,
            model_attribute="top_state",
        )
        self.auto_state: MainAutoState = MainAutoState.HomeAlone
        self.auto_machine = Machine(
            model=self,
            states=Scada.main_auto_states,
            transitions=Scada.main_auto_transitions,
            initial=MainAutoState.HomeAlone,
            send_event=False,
            model_attribute="auto_state",
        )
        

    def _start_derived_tasks(self):
        self._tasks.append(
            asyncio.create_task(self.report_sending_task(), name="reoirt_sender")
        )
        self._tasks.append(
            asyncio.create_task(self.snap_sending_task(), name="snap_sender")
        )
        self._tasks.append(
            asyncio.create_task(self.state_tracker(), name="scada top_state_tracker")
        )

    def process_scada_message(self, from_node: ShNode, payload: Any) -> None:
        """Process NamedTypes sent to primary scada"""
        # Todo: turn msg into GwBase
        match payload:
            case AdminDispatch():
                try:
                    self.admin_dispatch_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with admin_dispatch_received: \n {e}")
            case AdminKeepAlive():
                try:
                    self.admin_keep_alive_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with admin_keep_alive_received: \n {e}")
            case AdminReleaseControl():
                try:
                    self.admin_release_control_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with admin_release_control: \n {e}")
            case AllyGivesUp():
                try:
                    self.ally_gives_up_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with ally_gives_up_received: \n {e}")
            case AnalogDispatch():
                try:
                    self.analog_dispatch_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with analog_dispatch_received: \n {e}")
            case ChannelFlatlined():
                try:
                    self.data.flush_channel_from_latest(payload.Channel.Name)
                except Exception as e:
                    self.log(f"Trouble with ChannelFlatlined Received: \n {e}")
            case ChannelReadings():
                try:
                    self.channel_readings_received(from_node, payload)
                except Exception as e:
                    self.logger.error(f"problem with channel_readings_received: \n {e}")
            case DispatchContractGoDormant():
                try:
                    self.dispatch_contract_go_dormant_received(from_node, payload)
                except Exception as e:
                    self.logger.error(
                        f"problem with dispatch_contract_go_dormant_received: \n {e}"
                    )
            case DispatchContractGoLive():
                try:
                    self.dispatch_contract_go_live_received(from_node, payload)
                except Exception as e:
                    self.logger.error(
                        f"problem with dispatch_contract_go_live_received: \n {e}"
                    )
            case EnergyInstruction():
                try:
                    self.energy_instruction_received(from_node, payload)
                except Exception as e:
                    self.logger.error(
                        f"problem with .energy_instruction_received: \n {e}"
                    )
            case FsmFullReport():
                try:
                    self.fsm_full_report_received(from_node, payload)
                except Exception as e:
                    self.logger.error(f"problem with fsm_full_report_received: \n {e}")
            case HackOilOn():
                self.log("Received hack oil on")
                self._send_to(self.layout.atomic_ally, payload)
            case HackOilOff():
                self.log("Received hack oil off")
                self._send_to(self.layout.atomic_ally, payload)
            case MachineStates():
                try:
                    self.machine_states_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with machine_states_received: \n {e}")
            case PowerWatts():
                try:
                    self.power_watts_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with power_watts_received: \n {e}")
            case RemainingElec():
                try:
                    self.remaining_elec_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with remaining_elec_received: \n {e}")
            case ScadaParams():
                try:
                    self.scada_params_received(from_node, payload)
                    self._send_to(self.synth_generator, payload)
                except Exception as e:
                    self.log(f"Trouble with scada_params_received: \n {e}")
            case SendLayout():
                try:
                    self._send_to(from_node, self.layout_lite)
                except Exception as e:
                    self.log(f"Trouble with SendLayout: {e}")
            case SendSnap():
                try:
                    self._send_to(from_node, self._data.make_snapshot())
                except Exception as e:
                    self.log(f"Trouble with SendSnap: {e}")
            case SingleMachineState():
                try:
                    self.single_machine_state_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with single_machine_state_received: \n {e}")
            case SingleReading():
                try:
                    self.single_reading_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with single_reading_received: \n {e}")
            case SuitUp():
                try:
                    self.suit_up_received(from_node, payload)
                except Exception as e:
                    self.logger.error(f"Trouble with suit_up_received: \n {e}")
            case SyncedReadings():
                try:
                    self.synced_readings_received(from_node, payload)
                except Exception as e:
                    self.log(f"Trouble with synced_reading_received: \n {e}")
            case _:
                raise ValueError(f"Scada does not expect to receive[{type(payload)}!]")

    #####################################################################
    # Process Messages
    #####################################################################

    def admin_dispatch_received(
        self, from_node: ShNode, payload: AdminDispatch
    ) -> None:
        if from_node != self.admin:
            self.log(f"Ignoring AdminDispatch from {from_node.name}. Expected admin!")

        if not self.top_state == TopState.Admin:
            self.admin_wakes_up()
            self.log("Admin Wakes Up")
        self._renew_admin_timeout(timeout_seconds=payload.TimeoutSeconds)
        event = payload.DispatchTrigger
        self.log(f"AdminDispatch event is {event.EventName}")

        to_name = event.ToHandle.split(".")[-1]
        # TODO: change this to work if relays etc are NOT on primary scada
        if communicator := self.get_communicator(to_name):
            communicator.process_message(
                Message(
                    header=Header(
                        Src=H0N.admin,
                        Dst=communicator.name,
                        MessageType=event.TypeName,
                    ),
                    Payload=event,
                )
            )

    def admin_release_control_received(
        self, from_node: ShNode, payload: AdminReleaseControl
    ) -> None:
        if from_node != self.admin:
            self.log(
                f"Ignoring AdminReleaseControl from {from_node.Name} - expected admin"
            )
            return
        if self.top_state != TopState.Admin:
            self.log("Ignoring AdminReleaseControl, TopState not Admin")
            return
        # AdminReleasesControl:  Admin => Auto
        self.AdminReleasesControl()
        self.log(f"Admin releases control: {self.top_state}")
        # cancel the timeout
        if self._admin_timeout_task is not None:
            if not self._admin_timeout_task.cancelled():
                self._admin_timeout_task.cancel()
            self._admin_timeout_task = None
            # wake up auto state, which has been dormant. This will set
        # the actuator forest to HomeAlone
        self.auto_wakes_up()

    def admin_keep_alive_received(
        self, from_node: ShNode, payload: AdminKeepAlive
    ) -> None:
        if from_node != self.admin:
            self.log(f"Ignoring AdminKeepAlive from {from_node.name}. Expected admin!")

        self._renew_admin_timeout(timeout_seconds=payload.AdminTimeoutSeconds)
        self.log(f"Admin timeout renewed: {payload.AdminTimeoutSeconds} seconds")
        if not self.top_state == TopState.Admin:
            self.admin_wakes_up()
            self.log("Admin Wakes Up")

    def ally_gives_up_received(self, from_node: ShNode, payload: AllyGivesUp) -> None:
        if from_node.Name != H0N.atomic_ally:
            self.log(
                f"Ignoring AllyGivesUp from {from_node.Name} - expect AtomicAlly (aa)"
            )
            return
        if self.auto_state != MainAutoState.Atn:
            self.log(
                f"Ignoring AllyGivesUp from AtomicAlly, auto_state: {self.auto_state}"
            )
            return
        # AutoState transition: AllyGivesUp: Atn -> HomeAlone
        self.AllyGivesUp()
        self.log(f"Atomic Ally giving up control: {payload.Reason}")
        self.set_home_alone_command_tree()
        # wake up home alone again. Ally will already be dormant
        self._send_to(self.layout.home_alone, WakeUp(ToName=H0N.home_alone))
        # Inform AtomicTNode
        # TODO: send message like DispatchContractDeclined to Atn

    def analog_dispatch_received(
        self, from_node: ShNode, payload: AnalogDispatch
    ) -> None:
        if payload.FromGNodeAlias != self._layout.atn_g_node_alias:
            self.logger.error("IGNORING DISPATCH - NOT FROM MY ATN")
            return
        # HUGE HACK - 
        to_node = self.layout.node(payload.AboutName)
        boss_handle = '.'.join(to_node.handle.split('.')[:-1])
        self._send_to(to_node, AnalogDispatch(FromGNodeAlias=payload.FromGNodeAlias,
                                              FromHandle=boss_handle,
                                              ToHandle=to_node.handle,
                                              AboutName=to_node.name,
                                              Value=payload.Value,
                                              TriggerId=payload.TriggerId,
                                              UnixTimeMs=payload.UnixTimeMs))
        # to_node = self.layout.node_by_handle(payload.ToHandle)
        # if to_node:
        #     self.log(f"Sending to {to_node.Name}")
        #     self._send_to(to_node.Name, payload)

    def channel_readings_received(
        self, from_node: ShNode, payload: ChannelReadings
    ) -> None:
        if payload.ChannelName not in self._layout.data_channels:
            raise ValueError(
                f"Name {payload.ChannelName} in ChannelReadings not a recognized Data Channel!"
            )
        ch = self._layout.data_channels[payload.ChannelName]
        if from_node != ch.captured_by_node:
            raise ValueError(
                f"{payload.ChannelName} shoudl be read by {ch.captured_by_node}, not {from_node}!"
            )
        self._data.recent_channel_values[ch.Name] += payload.ValueList

        self._data.recent_channel_unix_ms[ch.Name] += payload.ScadaReadTimeUnixMsList
        if len(payload.ValueList) > 0:
            self._data.latest_channel_values[ch.Name] = payload.ValueList[-1]
            self._data.latest_channel_unix_ms[
                ch.Name
            ] = payload.ScadaReadTimeUnixMsList[-1]

    def dispatch_contract_go_dormant_received(
        self, from_node: ShNode, payload: DispatchContractGoDormant
    ) -> None:
        if payload.FromGNodeAlias != self.layout.atn_g_node_alias:
            self.log(f"HUH? Message from {payload.FromGNodeAlias}")
            return
        if self.auto_state != MainAutoState.Atn:
            self.log(
                f"Ignoring DispatchContractGoDormant from atn, auto_state: {self.auto_state}"
            )
            return
        self.AtnReleasesControl()
        self.set_home_alone_command_tree()
        self._send_to(self.layout.home_alone, WakeUp(ToName=H0N.home_alone))
        self._send_to(
            self.atomic_ally, GoDormant(FromName=self.name, ToName=H0N.atomic_ally)
        )

    def dispatch_contract_go_live_received(
        self, from_node: ShNode, payload: DispatchContractGoLive
    ) -> None:
        if payload.FromGNodeAlias != self.layout.atn_g_node_alias:
            self.log(f"HUH? Message from {payload.FromGNodeAlias}")
            return
        if self.auto_state != MainAutoState.HomeAlone:
            self.log(
                f"Ignoring control request from atn, auto_state: {self.auto_state}"
            )
            return
        self.atn_wants_control(t=payload)

    def energy_instruction_received(
        self, from_node: ShNode, payload: EnergyInstruction
    ) -> None:
        self._send_to(self.synth_generator, payload)
        if self.auto_state == MainAutoState.Atn:
            self._send_to(self.atomic_ally, payload)

    def fsm_full_report_received(
        self, from_node: ShNode, payload: FsmFullReport
    ) -> None:
        self._data.recent_fsm_reports[payload.TriggerId] = payload

    def machine_states_received(
        self, from_node: ShNode, payload: MachineStates
    ) -> None:
        node_name = payload.MachineHandle.split('.')[-1]
        if node_name in self._data.recent_machine_states:
            prev: MachineStates = self._data.recent_machine_states[
                node_name
            ]
            if payload.StateEnum != prev.StateEnum:
                raise Exception(
                    f"{payload.MachineHandle} has conflicting state machines!"
                    f"{payload.StateEnum} and {prev.StateEnum}"
                )

            self._data.recent_machine_states[node_name] = MachineStates(
                MachineHandle=payload.MachineHandle,
                StateEnum=payload.StateEnum,
                UnixMsList=prev.UnixMsList + payload.UnixMsList,
                StateList=prev.StateList + payload.StateList,
            )
        else:
            self._data.recent_machine_states[node_name] = payload
       
        self._data.latest_machine_state[node_name] = SingleMachineState(
            MachineHandle=payload.MachineHandle,
            StateEnum=payload.StateEnum,
            State=payload.StateList[-1],
            UnixMs=payload.UnixMsList[-1]
        )


    def power_watts_received(self, from_node: ShNode, payload: PowerWatts):
        """Highest priority of scada is to pass this on to Atn

        also update scada_data.power_watts, and send to synth gen
        """
        self._send_to(self.atn, payload)
        self._data.latest_total_power_w = payload.Watts
        self._send_to(self.synth_generator, payload)

    def remaining_elec_received(
        self, from_node: ShNode, payload: RemainingElec
    ) -> None:
        """Part of tracking the existing electricity contract

        Send to atn by generating an event (probably stop that?)
        Also share with atomic ally
        """
        if from_node.Name != H0N.synth_generator:
            self.log(
                f"Ignoring RemainingElecReceived from {from_node.Name} - expect {H0N.synth_generator}"
            )
        self._send_to(self.atomic_ally, payload)
        self.generate_event(RemainingElecEvent(Remaining=payload))
        self.log("Sent remaining elec to ATN and atomic ally")

    def scada_params_received(
        self, from_node: ShNode, payload: ScadaParams, testing: bool = False
    ) -> None:
        if from_node != self.atn:
            self.log(f"ScadaParams from {from_node.Name}; expect Atn!")
            return
        if payload.FromGNodeAlias != self.hardware_layout.atn_g_node_alias:
            self.log(
                f"ScadaParams from {payload.FromGNodeAlias}; expect {self.hardware_layout.atn_g_node_alias}!"
            )
            return
        new = payload.NewParams
        if new:
            old = self.data.ha1_params
            self.data.ha1_params = new
            if new.AlphaTimes10 != old.AlphaTimes10:
                self.update_env_variable("SCADA_ALPHA", new.AlphaTimes10 / 10)
            if new.BetaTimes100 != old.BetaTimes100:
                self.update_env_variable("SCADA_BETA", new.BetaTimes100 / 100)
            if new.GammaEx6 != old.GammaEx6:
                self.update_env_variable("SCADA_GAMMA", new.GammaEx6 / 1e6)
            if new.IntermediatePowerKw != old.IntermediatePowerKw:
                self.update_env_variable(
                    "SCADA_INTERMEDIATE_POWER", new.IntermediatePowerKw
                )
            if new.IntermediateRswtF != old.IntermediateRswtF:
                self.update_env_variable(
                    "SCADA_INTERMEDIATE_RSWT", new.IntermediateRswtF
                )
            if new.DdPowerKw != old.DdPowerKw:
                self.update_env_variable(
                    "SCADA_DD_POWER", new.DdPowerKw, testing=testing
                )
            if new.DdRswtF != old.DdRswtF:
                self.update_env_variable("SCADA_DD_RSWT", new.DdRswtF)
            if new.DdDeltaTF != old.DdDeltaTF:
                self.update_env_variable("SCADA_DD_DELTA_T", new.DdDeltaTF)
            if new.LoadOverestimationPercent != old.LoadOverestimationPercent:
                self.update_env_variable(
                    "SCADA_LOAD_OVERESTIMATION_PERCENT", new.LoadOverestimationPercent
                )

            response = ScadaParams(
                FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
                FromName=self.name,
                ToName=payload.FromName,
                UnixTimeMs=int(time.time() * 1000),
                MessageId=payload.MessageId,
                NewParams=self.data.ha1_params,
                OldParams=old,
            )
            self.logger.error(f"Sending back {response}")
            self._send_to(self.atn, response)

    def single_machine_state_received(
        self, from_node: ShNode, payload: SingleMachineState
    ) -> None:
        # TODO: compare MachineHandle last word with from_node.Name
        if payload.MachineHandle in self._data.recent_machine_states:
            prev: MachineStates = self._data.recent_machine_states[
                payload.MachineHandle
            ]
            if payload.StateEnum != prev.StateEnum:
                raise Exception(
                    f"{payload.MachineHandle} has conflicting state machines!"
                    f"{payload.StateEnum} and {prev.StateEnum}"
                )
            self._data.recent_machine_states[payload.MachineHandle] = MachineStates(
                MachineHandle=payload.MachineHandle,
                StateEnum=payload.StateEnum,
                UnixMsList=prev.UnixMsList + [payload.UnixMs],
                StateList=prev.StateList + [payload.State],
            )
        else:
            self._data.recent_machine_states[payload.MachineHandle] = MachineStates(
                MachineHandle=payload.MachineHandle,
                StateEnum=payload.StateEnum,
                StateList=[payload.State],
                UnixMsList=[payload.UnixMs],
            )
        node_name = payload.MachineHandle.split('.')[-1]
        self._data.latest_machine_state[node_name] = payload

    def single_reading_received(
        self, from_node: ShNode, payload: SingleReading
    ) -> None:
        if payload.ChannelName in self._layout.data_channels:
            ch = self._layout.data_channels[payload.ChannelName]
        elif payload.ChannelName in self._layout.synth_channels:
            ch = self._layout.synth_channels[payload.ChannelName]
        else:
            raise Exception(f"Missing channel name {payload.ChannelName}!")
        self._data.recent_channel_values[ch.Name].append(payload.Value)
        self._data.recent_channel_unix_ms[ch.Name].append(payload.ScadaReadTimeUnixMs)
        self._data.latest_channel_values[ch.Name] = payload.Value
        self._data.latest_channel_unix_ms[ch.Name] = payload.ScadaReadTimeUnixMs
        self._forward_single_reading(payload)

    def suit_up_received(self, from_node: ShNode, payload: SuitUp) -> None:
        if from_node.Name != H0N.atomic_ally:
            self.log(
                f"Ignoring AllyGivesUp from {from_node.Name} - expect AtomicAlly (aa)"
            )
            return
        # TODO: think through state machine
        # tell the atomic transactive node that game is on
        self._send_to(self.atn, GameOn(FromGNodeAlias=self.layout.scada_g_node_alias))

    def synced_readings_received(self, from_node: ShNode, payload: SyncedReadings):
        self._logger.path(
            "++synced_readings_received from: %s  channels: %d",
            from_node.Name,
            len(payload.ChannelNameList),
        )
        path_dbg = 0
        for idx, channel_name in enumerate(payload.ChannelNameList):
            path_dbg |= 0x00000001
            if channel_name not in self._layout.data_channels:
                raise ValueError(
                    f"Name {channel_name} in payload.SyncedReadings not a recognized Data Channel!"
                )
            ch = self._layout.data_channels[channel_name]
            self._data.recent_channel_values[ch.Name].append(payload.ValueList[idx])
            self._data.recent_channel_unix_ms[ch.Name].append(
                payload.ScadaReadTimeUnixMs
            )
            self._data.latest_channel_values[ch.Name] = payload.ValueList[idx]
            self._data.latest_channel_unix_ms[ch.Name] = payload.ScadaReadTimeUnixMs
        self._logger.path(
            "--gt_sh_telemetry_from_multipurpose_sensor_received  path:0x%08X", path_dbg
        )

    #####################################################################
    # State Machine related
    #####################################################################

    # Top States: Admin, Auto
    # Top Events: AdminWakesUp, AdminTimesOut, AdminReleasesControl

    def admin_wakes_up(self) -> None:
        if self.top_state == TopState.Admin:
            self.log("Ignoring AdminWakesUp, TopState already Admin")
            return
        # Trigger the AdminWakesUp event for top state:  Auto => Admin
        self.AdminWakesUp()
        self.log(f"Message from Admin! top_state {self.top_state}")
        if self.auto_state == MainAutoState.Dormant:
            self.log("AdminWakesUp called when auto state was dormant!!")
            return
        # This will set auto_state and update the actuator forest to Admin
        self.auto_goes_dormant()
        
        # Uncomment if we want strat boss to stop when switching to admin
        # strat_boss = self.layout.node(H0N.strat_boss)
        # admin = self.layout.node(H0N.admin)
        # self._send_to(strat_boss,
        #               StratBossTrigger(
        #                   FromState=StratBossState.Active,
        #                   ToState=StratBossState.Dormant,
        #                   Trigger=StratBossEvent.BossCancels,
        #               ),
        #               admin)

    def admin_releases_control(self) -> None:
        if self.top_state != TopState.Admin:
            self.log("Ignoring AdminWakesUp, TopState not Admin")
            return
        # AdminReleasesControl:  Admin => Auto
        self.AdminReleasesControl()
        self.log(f"Admin releases control: {self.top_state}")
        # cancel the timeout
        if self._admin_timeout_task is not None:
            if not self._admin_timeout_task.cancelled():
                self._admin_timeout_task.cancel()
            self._admin_timeout_task = None
            # wake up auto state, which has been dormant. This will set
        # the actuator forest to HomeAlone
        self.auto_wakes_up()

    def admin_times_out(self) -> None:
        if self.top_state == TopState.Auto:
            self.log("Ignoring AdminTimesOut, TopState already Auto")
            return

        # AdminTimesOut: Admin => Auto
        self.AdminTimesOut()
        self.log(f"Admin timed out! {self.top_state}")
        # cancel the timeout
        if self._admin_timeout_task is not None:
            if not self._admin_timeout_task.cancelled():
                self._admin_timeout_task.cancel()
            self._admin_timeout_task = None

        # wake up auto state, which has been dormant. This will set
        # the actuator forest to HomeAlone
        self.auto_wakes_up()

    # AUTO STATE MACHINE

    def auto_wakes_up(self) -> None:
        if self.auto_state != MainAutoState.Dormant:
            self.log(f"STRANGE!! auto state is already{self.auto_state}")
            return

        # Trigger AutoWakesUp for auto state: Dormant -> HomeAlone
        self.AutoWakesUp()
        # all actuators report directly to home alone
        self.set_home_alone_command_tree()
        # Let homealone and pico-cycler know they in charge again
        self._send_to(self.layout.home_alone, WakeUp(ToName=H0N.home_alone))
        self._send_to(self.layout.pico_cycler, WakeUp(ToName=H0N.pico_cycler))

    def auto_goes_dormant(self) -> None:
        if self.auto_state == MainAutoState.Dormant:
            self.log("Ignoring AutoGoesDormant ... auto state is already dormant")
            return
        # Trigger AutoGoesDormant for auto state: Atn OR HomeAlone -> Dormant
        self.AutoGoesDormant()
        self.log(f"auto_state {self.auto_state}")
        # ADMIN CONTROL FOREST: a single tree, controlling all actuators
        self.set_admin_command_tree()

        # Let the active nodes know they've lost control of their actuators
        for direct_report in [
            self.layout.atomic_ally,
            self.layout.home_alone,
            self.layout.pico_cycler,
        ]:
            self._send_to(
                direct_report, GoDormant(FromName=self.name, ToName=direct_report.Name)
            )

    def ally_gives_up(self, msg: AllyGivesUp) -> None:
        if self.auto_state != MainAutoState.Atn:
            self.log(
                f"Ignoring AllyGivesUp message, auto_state: {self.auto_state}"
            )
            return
        # AutoState transition: AllyGivesUp: Atn -> HomeAlone
        self.AllyGivesUp()
        self.log(f"Atomic Ally giving up control: {msg.Reason}")
        self.set_home_alone_command_tree()
        # wake up home alone again. Ally will already be dormant
        self._send_to(self.layout.home_alone, WakeUp(ToName=H0N.home_alone))
        # Inform AtomicTNode
        # TODO: send message like DispatchContractDeclined to Atn

    def atn_wants_control(self, t: DispatchContractGoLive) -> None:
        if t.FromGNodeAlias != self.layout.atn_g_node_alias:
            self.log(f"HUH? Message from {t.FromGNodeAlias}")
            return
        if self.auto_state != MainAutoState.HomeAlone:
            self.log(
                f"Ignoring control request from atn, auto_state: {self.auto_state}"
            )
            return

        # Trigger AtnWantsControl for auto state: HomeAlone -> Atn
        self.AtnWantsControl()
        self.log(f"AtnWantsControl! Auto state {self.auto_state}")
        # ATN CONTROL FOREST: pico cycler its own tree. All other actuators report to Atomic
        # Ally which reports to atn.
        self.set_atn_command_tree()
        # Let homealone know its dormant:
        self._send_to(
            self.layout.home_alone, GoDormant(FromName=self.name, ToName=H0N.home_alone)
        )
        # Let the atomic ally know its live
        self._send_to(self.layout.atomic_ally, WakeUp(ToName=H0N.atomic_ally))

    def atn_link_dead(self) -> None:
        if self.auto_state != MainAutoState.Atn:
            self.log(f"Atn link is dead, but we were in state {self.auto_state} anyway")
            return

        # Trigger AtnLinkDead auto state:  Atn -> HomeAlone
        self.AtnLinkDead()
        self.log(f"AtnLink id dead! Auto state {self.auto_state}")
        self.set_home_alone_command_tree()
        # Let home alone know its in charge
        self._send_to(self.layout.home_alone, WakeUp(ToName=H0N.home_alone))
        self._send_to(
            self.layout.atomic_ally,
            GoDormant(FromName=H0N.primary_scada, ToName=H0N.atomic_ally),
        )
        # Pico Cycler shouldn't change

    def _derived_recv_deactivated(
        self, transition: LinkManagerTransition
    ) -> Result[bool, BaseException]:
        """Overwrites base method. Triggered when link state is deactivated"""
        if transition.link_name == self.upstream_client:
            # proactor-speak for Atn is no longer talking with Scada, as evidenced
            # by the once-a-minute pings disappearing
            self.atn_link_dead()
        return Ok()

    def _derived_recv_activated(
        self, transition: Transition
    ) -> Result[bool, BaseException]:
        """Overwrites base method. Triggered when link state is activated"""
        if transition.link_name == self.upstream_client:
            self._send_to(self.atn, self.layout_lite)
        return Ok()

    ###########################################################
    # Command Trees - the handles of the Spaceheat Nodes form a tree
    # where the line of direct report is required for following a command
    ##########################################################

    def set_home_alone_command_tree(self) -> None:
        """ HomeAlone Base Command Tree
        
         - All actuators except for HpScadaOps and PicoCycler report to AtomicAlly
         - HpRelayBoss reports to Atomic Ally, 
         - StratBoss reports to Atomic Ally
        
         TODO: Add ascii representation 
        """

        hp_relay_boss = self.layout.node(H0N.hp_relay_boss)
        hp_relay_boss.Handle = f"{H0N.auto}.{H0N.home_alone}.{hp_relay_boss.Name}"
        
        strat_boss = self.layout.node(H0N.strat_boss)
        strat_boss.Handle = f"{H0N.auto}.{H0N.home_alone}.{strat_boss.Name}"

        for node in self.layout.actuators:
            if node.Name == H0N.vdc_relay:
                node.Handle = f"{H0N.auto}.{H0N.pico_cycler}.{node.Name}"
            elif node.Name == H0N.hp_scada_ops_relay:
                node.Handle = f"{H0N.auto}.{H0N.home_alone}.{hp_relay_boss.Name}.{node.Name}"
            else:
                node.Handle = (
                    f"{H0N.auto}.{H0N.home_alone}.{H0N.home_alone_normal}.{node.Name}"
                )
        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )

    def set_admin_command_tree(self) -> None:
        """ Admin Base Command Tree
        
         - All actuators except for HpScadaOps report directly to admin
         - HpRelayBoss reports to admin
         - StratBoss reports to admin
        """
        hp_relay_boss = self.layout.node(H0N.hp_relay_boss)
        hp_relay_boss.Handle = f"{H0N.admin}.{hp_relay_boss.Name}"
        
        strat_boss = self.layout.node(H0N.strat_boss)
        strat_boss.Handle = f"{H0N.admin}.{strat_boss.Name}"

        for node in self.layout.actuators:
            if node.Name == H0N.hp_scada_ops_relay:
                node.Handle = f"{H0N.admin}.{hp_relay_boss.Name}.{node.Name}"
            else:
                node.Handle = f"{H0N.admin}.{node.Name}"
        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )

    def set_atn_command_tree(self) -> None:
        """ Atn Base Command Tree
        
         - All actuators except for HpScadaOps and PicoCycler report to AtomicAlly
         - HpRelayBoss reports to Atomic Ally, 
         - StratBoss reports to Atomic Ally
         TODO: Add ascii representation 
        """
        hp_relay_boss = self.layout.node(H0N.hp_relay_boss)
        hp_relay_boss.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{hp_relay_boss.Name}"
        
        strat_boss = self.layout.node(H0N.strat_boss)
        strat_boss.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{strat_boss.Name}"

        for node in self.layout.actuators:
            if node.Name == H0N.vdc_relay:
                node.Handle = f"{H0N.auto}.{H0N.pico_cycler}.{node.Name}"
            elif node.Name == H0N.hp_scada_ops_relay:
                node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{hp_relay_boss.Name}.{node.Name}"
            else:
                node.Handle = f"{H0N.atn}.{H0N.atomic_ally}.{node.Name}"
        self._send_to(
            self.atn,
            NewCommandTree(
                FromGNodeAlias=self.layout.scada_g_node_alias,
                ShNodes=list(self.layout.nodes.values()),
                UnixMs=int(time.time() * 1000),
            ),
        )

    async def state_tracker(self) -> None:
        loop_s = self.settings.seconds_per_report
        while True:
            hiccup = 1.5
            sleep_s = max(hiccup, loop_s - (time.time() % loop_s) - 1.2)
            await asyncio.sleep(sleep_s)
            # report the state
            if sleep_s != hiccup:
                self._send_to(
                    self.node,
                    MachineStates(
                        MachineHandle=self.node.handle,
                        StateEnum=TopState.enum_name(),
                        StateList=[self.top_state],
                        UnixMsList=[int(time.time() * 1000)],
                    ),
                )

                self._send_to(
                    self.node,
                    MachineStates(
                        MachineHandle=self.layout.auto_node.handle,
                        StateEnum=MainAutoState.enum_name(),
                        StateList=[self.auto_state],
                        UnixMsList=[int(time.time() * 1000)],
                    ),
                )
                self.logger.warning(f"Top state: {self.top_state}")
                self.logger.warning(f"Auto state: {self.auto_state}")

    #############################################
    # Core synchronous reporting tasks: reports (all timestamped sensing data)
    # and snapshots (latest snapshots)
    ##############################################

    def next_report_second(self) -> int:
        last_report_second_nominal = int(
            self._last_report_second
            - (self._last_report_second % self.settings.seconds_per_report)
        )
        return last_report_second_nominal + self.settings.seconds_per_report

    def next_snap_second(self) -> int:
        last_snap_nominal = int(
            self._last_snap_s - (self._last_snap_s % self.settings.seconds_per_snapshot)
        )
        return last_snap_nominal + self.settings.seconds_per_snapshot

    def seconds_til_next_report(self) -> float:
        return self.next_report_second() - time.time()

    def seconds_til_next_snap(self) -> float:
        return self.next_snap_second() - time.time()

    def time_to_send_report(self) -> bool:
        return time.time() > self.next_report_second()

    def time_to_send_snap(self) -> bool:
        return time.time() > self.next_snap_second()

    def send_report(self):
        report = self._data.make_report(self._last_report_second)
        self._data.reports_to_store[report.Id] = report
        self.generate_event(ReportEvent(Report=report))  # noqa
        self._data.flush_recent_readings()

    def send_snap(self):
        snapshot = self._data.make_snapshot()
        self._send_to(self.atn, snapshot)
        if self.settings.admin.enabled:
            self._send_to(self.admin, snapshot)

    async def report_sending_task(self):
        while not self._stop_requested:
            try:
                if self.time_to_send_report():
                    self.send_report()
                    self._last_report_second = int(time.time())
                await asyncio.sleep(self.seconds_til_next_report())
            except Exception as e:
                self.log(e)

    async def snap_sending_task(self):
        while not self._stop_requested:
            try:
                if self.time_to_send_snap():
                    self.send_snap()
                    self._last_snap_s = int(time.time())
                await asyncio.sleep(self.seconds_til_next_snap())
            except Exception as e:
                self.log(e)

    #####################################################################
    # Basic plumbing - mostly about messages
    #####################################################################

    def _send_to(self, to_node: ShNode, payload: Any, from_node: ShNode = None) -> None:
        """Use this for primary_scada to send messages"""
        if to_node is None:
            return
        if from_node is None:
            from_node = self.node

        # HACK FOR nodes whose 'actors' are handled by their parent's communicator
        communicator_by_name = {to_node.Name: to_node.Name}
        communicator_by_name[H0N.home_alone_normal] = H0N.home_alone
    
        # if the message is meant for primary_scada, process here
        if to_node.name == self.name:
            self.process_scada_message(from_node, payload)
        
        # if its meant for an actor spawned by primary_scada (aka communicator)
        # call its process_message
        elif communicator_by_name[to_node.Name] in set(self._communicators.keys()):
            self.get_communicator(communicator_by_name[to_node.Name]).process_message(
                Message(Src=from_node.Name, Dst=to_node.Name, Payload=payload)
            )
        elif to_node.Name == H0N.admin:
            self._links.publish_message(
                link_name=self.ADMIN_MQTT,
                message=Message(
                    Src=self.publication_name, Dst=to_node.Name, Payload=payload
                ),
                qos=QOS.AtMostOnce,
            )
        elif to_node.Name == H0N.atn:
            #self._links.publish_upstream(payload)
            self._links.publish_message(
                link_name=self.ATN_MQTT,
                message=Message(
                    Src=self.publication_name, Dst=to_node.Name, Payload=payload
                ),
                qos=QOS.AtMostOnce,
            )
        else:  # publish to local for actors on LAN not run by primary_scada
            self._links.publish_message(
                link_name=Scada.LOCAL_MQTT,
                message=Message(Src=from_node.Name, Dst=to_node.Name, Payload=payload),
                qos=QOS.AtMostOnce,
                use_link_topic=True,
            )

    def _derived_process_message(self, message: Message):
        """Plumbing: messages received on the internal proactor queue

        Replaces proactor _derived_process_message. Either routes to the appropriate
        node or - if message is intended for primary scada - sends on to _process_my_message
        """
        from_node = self._layout.node(message.Header.Src, None)
        to_node = self._layout.node(message.Header.Dst, None)

        if to_node is not None and to_node != self.node:
            try:
                self._send_to(to_node, message.Payload, from_node)
            except Exception as e:
                print(f"Problem with message to {to_node.name}")
                print(f"message {message}")
                print(f"payload {message.Payload}")
                raise e
        else:
            self.process_scada_message(from_node=from_node, payload=message.Payload)

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Message[Any]
    ) -> None:

        to_node = self._layout.node(message.Header.Dst, None)
        if to_node is None:
            to_node = self.node
        payload = decoded.Payload
        src = decoded.Header.Src
        if message.Payload.client_name == self.LOCAL_MQTT:
            # store and pass on all the events from scada2
            if isinstance(decoded.Payload, EventBase):
                self.generate_event(decoded.Payload)
                return
        elif message.Payload.client_name == self.ATN_MQTT:
            if src != self.layout.atn_g_node_alias:
                self.log(
                    f"IGNORING message from upstream. Expected {self.layout.atn_g_node_alias} but got {src}"
                )
                return
            src = H0N.atn
        elif message.Payload.client_name == self.ADMIN_MQTT:
            if not self.settings.admin.enabled:
                return
            src = H0N.admin
            # TODO: make admin conversation less hacky?
            if decoded.Payload.TypeName == "strat.boss.trigger":
                to_node = self.layout.node(H0N.strat_boss)
        else:
            raise ValueError(
                "ERROR. No mqtt handler for mqtt client %s", message.Payload.client_name
            )
        from_node = self._layout.node(src, None)

        if from_node is None:
            self.log(f"Got a message from unrecognized {decoded.Header.Src} - ignoring")
            self.decoded = decoded
            return

        self._send_to(to_node, payload, from_node)

    def init(self) -> None:
        """Called after constructor so derived functions can be used in setup."""

    @classmethod
    def make_event_persister(cls, settings: ScadaSettings) -> TimedRollingFilePersister:
        return TimedRollingFilePersister(
            settings.paths.event_dir,
            max_bytes=settings.persister.max_bytes,
            pat_watchdog_args=SystemDWatchdogCommandBuilder.pat_args(
                str(settings.paths.name)
            ),
        )

    def run_in_thread(self, daemon: bool = True) -> threading.Thread:
        """Basic function for running the scada"""

        async def _async_run_forever():
            try:
                await self.run_forever()

            finally:
                self.stop()

        def _run_forever():
            asyncio.run(_async_run_forever())

        thread = threading.Thread(target=_run_forever, daemon=daemon)
        thread.start()
        return thread

    #####################################################################
    # Admin related
    #####################################################################

    async def _timeout_admin(self, timeout_seconds: Optional[int] = None) -> None:
        if (
            timeout_seconds is None
            or timeout_seconds > self.settings.admin.max_timeout_seconds
        ):
            await asyncio.sleep(self.settings.admin.max_timeout_seconds)
        else:
            await asyncio.sleep(timeout_seconds)
        if self.top_state == TopState.Admin:
            self.admin_times_out()

    def _renew_admin_timeout(self, timeout_seconds: Optional[int] = None):
        if self._admin_timeout_task is not None:
            self._admin_timeout_task.cancel()
        self._admin_timeout_task = asyncio.create_task(
            self._timeout_admin(timeout_seconds)
        )

    def _forward_single_reading(self, reading: SingleReading) -> None:
        if (
            self.settings.admin.enabled
            and reading.ChannelName in self._layout.data_channels
        ):
            if (
                self._layout.node(
                    self._layout.data_channels[reading.ChannelName].AboutNodeName
                ).ActorClass
                == ActorClass.Relay
            ):
                self._send_to(self.admin, reading)

    #################################################
    # Various properties
    #################################################

    @property
    def name(self):
        return self._name

    @property
    def node(self) -> ShNode:
        return self._node

    @property
    def publication_name(self) -> str:
        return self._layout.scada_g_node_alias

    @property
    def subscription_name(self) -> str:
        return H0N.primary_scada

    @property
    def settings(self) -> ScadaSettings:
        return cast(ScadaSettings, self._settings)

    @property
    def hardware_layout(self) -> House0Layout:
        return self._layout

    @property
    def layout(self) -> House0Layout:
        return self._layout

    @property
    def admin(self) -> ShNode:
        return self.layout.node(H0N.admin)

    @property
    def atn(self) -> ShNode:
        return self.layout.node(H0N.atn)

    @property
    def atomic_ally(self) -> ShNode:
        return self.layout.node(H0N.atomic_ally)

    @property
    def home_alone(self) -> ShNode:
        return self.layout.node(H0N.home_alone)

    @property
    def synth_generator(self) -> ShNode:
        return self.layout.node(H0N.synth_generator)

    @property
    def data(self) -> ScadaData:
        return self._data

    @property
    def layout_lite(self) -> LayoutLite:
        tank_nodes = [
            node
            for node in self.layout.nodes.values()
            if node.ActorClass == ActorClass.ApiTankModule
        ]
        flow_nodes = [
            node
            for node in self.layout.nodes.values()
            if node.ActorClass == ActorClass.ApiFlowModule
        ]
        return LayoutLite(
            FromGNodeAlias=self.layout.scada_g_node_alias,
            FromGNodeInstanceId=self.layout.scada_g_node_id,
            Strategy=self.layout.strategy,
            ZoneList=self.layout.zone_list,
            TotalStoreTanks=self.layout.total_store_tanks,
            TankModuleComponents=[node.component.gt for node in tank_nodes],
            FlowModuleComponents=[node.component.gt for node in flow_nodes],
            ShNodes=[node.to_gt() for node in self.layout.nodes.values()],
            DataChannels=[ch.to_gt() for ch in self.layout.data_channels.values()],
            SynthChannels=[ch.to_gt() for ch in self.layout.synth_channels.values()],
            Ha1Params=self.data.ha1_params,
            I2cRelayComponent=self.layout.node(H0N.relay_multiplexer).component.gt,
            MessageCreatedMs=int(time.time() * 1000),
            MessageId=str(uuid.uuid4()),
        )

    ################################################
    # Hacky stuff
    ###############################################

    def update_env_variable(self, variable, new_value, testing: bool = False) -> None:
        """
        Updates .env with new Scada Params.
        TODO: move this somewhere else, like a local sqlite db
        """
        if testing:
            dotenv_filepath = dotenv.find_dotenv(usecwd=True)
            if not dotenv_filepath:
                self.logger.error("Couldn't find a .env file - perhaps because in CI?")
                return
        else:
            dotenv_filepath = "/home/pi/gw-scada-spaceheat-python/.env"
            if not os.path.isfile(dotenv_filepath):
                self.log("Did not find .env file")
                return
        with open(dotenv_filepath, "r") as file:
            lines = file.readlines()
        with open(dotenv_filepath, "w") as file:
            line_exists = False
            for line in lines:
                if line.replace(" ", "").startswith(f"{variable}="):
                    file.write(f"{variable}={new_value}\n")
                    line_exists = True
                else:
                    file.write(line)
            if not line_exists:
                file.write(f"\n{variable}={new_value}\n")

    def log(self, note: str) -> None:
        log_str = f"[scada] {note}"
        self.services.logger.error(log_str)
