"""Scada implementation"""

import asyncio
import enum
import uuid
import threading
import time
from typing import Any
from typing import List
from typing import Optional
import dotenv
from enum import auto
from gwproto.message import Header
from gwproactor.external_watchdog import SystemDWatchdogCommandBuilder
from gwproactor.links import LinkManagerTransition
from gwproactor.links.link_settings import LinkSettings
from gwproactor.message import InternalShutdownMessage
from gwproto import create_message_model
from gwproto import MQTTTopic
from gwproto.enums import ActorClass, MainAutoState
from gwproto.data_classes.house_0_names import H0N
from gwproto.data_classes.house_0_layout import House0Layout
from gwproto.messages import FsmAtomicReport, FsmEvent, FsmFullReport
from gwproto.messages import EventBase
from gwproto.messages import LayoutLite
from gwproto.message import Message
from gwproto.messages import PowerWatts
from gwproto.messages import SendSnap, SendLayout

from gwproto.named_types import (AdminWakesUp, AnalogDispatch, ChannelReadings, MachineStates, 
                                 PicoMissing, ScadaParams, SingleReading, SyncedReadings,
                                TicklistReedReport, TicklistHallReport)

from gwproto.named_types import GoDormant, DormantAck

from gwproto.messages import ReportEvent


from admin.messages import AdminCommandReadRelays
from admin.messages import AdminCommandSetRelay
from admin.messages import RelayStates

from actors.api_flow_module import TicklistHall, TicklistReed
from gwproto import MQTTCodec
from result import Ok
from result import Result

from gwproactor import ActorInterface
from gw.enums import GwStrEnum
from actors.api_tank_module import MicroVolts
from actors.scada_data import ScadaData
from actors.scada_interface import ScadaInterface
from actors.config import ScadaSettings
from gwproto.data_classes.sh_node import ShNode
from gwproactor import QOS

from gwproactor.links import Transition
from gwproactor.message import MQTTReceiptPayload
from gwproactor.persister import TimedRollingFilePersister
from gwproactor.proactor_implementation import Proactor
from transitions import Machine


ScadaMessageDecoder = create_message_model(
    "ScadaMessageDecoder",
    [
        "gwproto.messages",
        "gwproactor.message",
        "actors.message",
        "admin.messages",
    ]
)

SYNC_SNAP_S = 30

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


class MainAutoEvent(GwStrEnum):
    AtnLinkDead = auto()
    AtnDispatchRequest = auto()
    GoDormant = auto()
    WakeUp = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "main.auto.event"
    
class TopState(GwStrEnum):
    Auto = auto()
    Admin = auto()
    ChangingToAdmin = auto()
    ChangingToAuto = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "top.state"

class TopEvent(GwStrEnum):
    AdminWakesUp = auto()
    AutoWakesUp = auto()
    ChangeToAuto = auto()
    ChangeToAdmin = auto()

    @classmethod
    def enum_name(cls) -> str:
        return "top.event"

class Scada(ScadaInterface, Proactor):
    ASYNC_POWER_REPORT_THRESHOLD = 0.05
    DEFAULT_ACTORS_MODULE = "actors"
    GRIDWORKS_MQTT = "gridworks"
    LOCAL_MQTT = "local"
    ADMIN_MQTT = "admin"

    _data: ScadaData
    _last_report_second: int
    _last_sync_snap_s: int
    _dispatch_live_hack: bool
    _channels_reported: bool

    top_states = ["Auto", "Admin", "ChangingToAdmin", "ChangingToAuto"]
    top_transitions = [
        {"trigger": "AdminWakesUp", "source": "Auto", "dest": "ChangingToAdmin"},
        {"trigger": "ChangeToAdmin", "source": "ChangingToAdmin", "dest": "Admin"},
        {"trigger": "AutoWakesUp", "source": "Admin", "dest": "ChangingToAuto"},
        {"trigger": "ChangeToAuto", "source": "ChangingToAuto", "dest": "Admin"},
    ]

    main_auto_states = ["Atn", "HomeAlone", "Dormant"]
    main_auto_transitions = [
        {"trigger": "AtnLinkDead", "source": "Atn", "dest": "HomeAlone"},
        {"trigger": "AtnDispatchRequest", "source": "HomeAlone", "dest": "Atn"},
        {"trigger": "GoDormant", "source": "Atn", "dest": "Dormant"},
        {"trigger": "GoDormant", "source": "HomeAlone", "dest": "Dormant"},
        {"trigger": "WakeUp", "source": "Dormant", "dest": "HomeAlone"}
    ]
    def __init__(
        self,
        name: str,
        settings: ScadaSettings,
        hardware_layout: House0Layout,
        actor_nodes: Optional[List[ShNode]] = None,
    ):
        print(f"actor_nodes are {actor_nodes}")
        if not isinstance(hardware_layout, House0Layout):
            raise Exception("Make sure to pass Hosue0Layout object as hardware_layout!")
        self.is_simulated = False
        self._layout: House0Layout = hardware_layout
        self._data = ScadaData(settings, hardware_layout)
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        remote_actor_node_names = {node.name for node in self._layout.nodes.values() if
                   self._layout.parent_node(node) != self._node and
                   node != self._node and
                   node.has_actor}
        self._links.add_mqtt_link(
            LinkSettings(
                client_name=self.LOCAL_MQTT,
                gnode_name=H0N.secondary_scada,
                spaceheat_name=H0N.secondary_scada,
                mqtt=self.settings.local_mqtt,
                codec=LocalMQTTCodec(
                    primary_scada=True,
                    remote_node_names=remote_actor_node_names
                ),
                downstream=True,
            )
        )
        self._links.add_mqtt_link(
            LinkSettings(
                client_name=self.GRIDWORKS_MQTT,
                gnode_name=self._layout.atn_g_node_alias,
                spaceheat_name=H0N.atn,
                mqtt=self.settings.gridworks_mqtt,
                codec=GridworksMQTTCodec(self._layout),
                upstream=True,
            )
        )
        for node_name in remote_actor_node_names:
            self._links.subscribe(
                client=self.LOCAL_MQTT,
                topic=MQTTTopic.encode(
                    envelope_type=Message.type_name(),
                    src=node_name,
                    dst=self.subscription_name,
                    message_type="#",
                ),
                qos=QOS.AtMostOnce,
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
        self._last_sync_snap_s = int(now)
        self._dispatch_live_hack = False
        self.pending_dispatch: Optional[AnalogDispatch] = None
        if actor_nodes is not None:
            for actor_node in actor_nodes:
                self.add_communicator(
                    ActorInterface.load(
                        actor_node.Name,
                        str(actor_node.actor_class),
                        self,
                        self.DEFAULT_ACTORS_MODULE
                    )
                )
        self.top_machine = Machine(
            model=self,
            states=Scada.top_states,
            transitions=Scada.top_transitions,
            initial=TopState.Auto,
            send_event=False,
            model_attribute="top_state",
        )
        self.auto_machine = Machine(
            model=self,
            states=Scada.main_auto_states,
            transitions=Scada.main_auto_transitions,
            initial=MainAutoState.HomeAlone,
            send_event=False,
            model_attribute="auto_state",
        )



    def init(self) -> None:
        """Called after constructor so derived functions can be used in setup."""
        print("hi!")

    @classmethod
    def make_event_persister(cls, settings: ScadaSettings) -> TimedRollingFilePersister:
        return TimedRollingFilePersister(
            settings.paths.event_dir,
            max_bytes=settings.persister.max_bytes,
            pat_watchdog_args=SystemDWatchdogCommandBuilder.pat_args(
                str(settings.paths.name)
            ),
        )

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
    def settings(self):
        return self._settings

    @property
    def hardware_layout(self) -> House0Layout:
        return self._layout
    
    @property
    def layout(self) -> House0Layout:
        return self._layout
    
    @property
    def auto_node(self) -> ShNode:
        if H0N.auto not in self._layout.nodes:
            raise Exception(f"Missing {H0N.auto} Node")
        return self._layout.node(H0N.auto)

    @property
    def data(self) -> ScadaData:
        return self._data

    def _start_derived_tasks(self):
        self._tasks.append(
            asyncio.create_task(self.update_report(), name="update_report")
        )
        self._tasks.append(
            asyncio.create_task(self.update_snap(), name="update_snap")
        )
        self._tasks.append(
            asyncio.create_task(self.state_tracker(), name="scada top_state_tracker")
        )

    async def update_report(self):
        while not self._stop_requested:
            try:
                if self.time_to_send_snap():
                    self.send_snap()
                    self._last_sync_snap_s = int(time.time())
                if self.time_to_send_report():
                    self.send_report()
                    self._last_report_second = int(time.time())
                await asyncio.sleep(self.seconds_til_next_report())
            except Exception as e:
                try:
                    if not isinstance(e, asyncio.CancelledError):
                        self._logger.exception(e)
                        self._send(
                            InternalShutdownMessage(
                                Src=self.name,
                                Reason=(
                                    f"update_report() task got exception: <{type(e)}> {e}"
                                ),
                            )
                        )
                finally:
                    break
    
    async def update_snap(self):
        while not self._stop_requested:
            try:
                if self.time_to_send_snap():
                    self.send_snap()
                await asyncio.sleep(5)
            except Exception as e:
                try:
                    if not isinstance(e, asyncio.CancelledError):
                        self._logger.exception(e)
                        self._send(
                            InternalShutdownMessage(
                                Src=self.name,
                                Reason=(
                                    f"update_report() task got exception: <{type(e)}> {e}"
                                ),
                            )
                        )
                finally:
                    break

    def send_layout_info(self) -> None:
        tank_nodes = [node for node in self._layout.nodes.values() if node.ActorClass == ActorClass.ApiTankModule]
        flow_nodes = [node for node in self._layout.nodes.values() if node.ActorClass == ActorClass.ApiFlowModule]
        if H0N.relay_multiplexer in self.layout.nodes.keys():
            layout = LayoutLite(
                FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
                FromGNodeInstanceId=self.hardware_layout.scada_g_node_id,
                Strategy=self._layout.strategy,
                ZoneList=self._layout.zone_list,
                TotalStoreTanks=self._layout.total_store_tanks,
                TankModuleComponents=[node.component.gt for node in tank_nodes],
                FlowModuleComponents=[node.component.gt for node in flow_nodes],
                ShNodes=[node.to_gt() for node in self.layout.nodes.values()],
                DataChannels=[ch.to_gt() for ch in self.data.my_data_channels],
                SynthChannels=[ch.to_gt() for ch in self.data.my_synth_channels],
                Ha1Params=self.data.ha1_params,
                I2cRelayComponent=self.hardware_layout.node(H0N.relay_multiplexer).component.gt,
                MessageCreatedMs=int(time.time() * 1000),
                MessageId=str(uuid.uuid4())
            )
            self._links.publish_upstream(layout)
            #self.generate_event(LayoutEvent(Layout=layout))
            self.logger.error("Just sent layout")

    def send_report(self):
        report = self._data.make_report(self._last_report_second)
        self._data.reports_to_store[report.Id] = report
        self.generate_event(ReportEvent(Report=report))
        self._publish_to_local(self._node, report)
        self._data.flush_latest_readings()
    
    def send_snap(self):
        snapshot = self._data.make_snapshot()
        self._publish_to_local(self._node, snapshot)
        self._links.publish_upstream(snapshot)

    def next_report_second(self) -> int:
        last_report_second_nominal = int(
            self._last_report_second
            - (self._last_report_second % self.settings.seconds_per_report)
        )
        return last_report_second_nominal + self.settings.seconds_per_report

    def next_sync_snap_s(self) -> int:
        last_sync_snap_s = int(
            self._last_sync_snap_s
            - (self._last_sync_snap_s % SYNC_SNAP_S)
        )
        return last_sync_snap_s + SYNC_SNAP_S

    def seconds_til_next_report(self) -> float:
        return self.next_report_second() - time.time()

    def time_to_send_report(self) -> bool:
        return time.time() > self.next_report_second()
    
    def time_to_send_snap(self) -> bool:
        if time.time() > self.next_sync_snap_s():
            self._last_sync_snap_s = int(time.time())
            return True
        #TODO: add sending on change.

    def _publish_to_local(self, from_node: ShNode, payload, qos: QOS = QOS.AtMostOnce):
        message = Message(Src=from_node.Name, Payload=payload)
        return self._links.publish_message(Scada.LOCAL_MQTT, message, qos=qos)

    def _derived_process_message(self, message: Message):
        self._logger.path("++Scada._derived_process_message %s/%s", message.Header.Src, message.Header.MessageType)
        path_dbg = 0
        from_node = self._layout.node(message.Header.Src, None)
        match message.Payload:
            case PowerWatts():
                path_dbg |= 0x00000001
                if from_node is self._layout.power_meter_node:
                    path_dbg |= 0x00000002
                    self.power_watts_received(message.Payload)
                else:
                    raise Exception(
                        f"message.Header.Src {message.Header.Src} must be from {self._layout.power_meter_node} for PowerWatts message"
                    )
            case AnalogDispatch():
                path_dbg |= 0x10000000
                try:
                    self.get_communicator(message.Header.Dst).process_message(message)
                except Exception as e:
                    self.logger.error(f"Problem with  {message.Header}: {e}")
            case ChannelReadings():
                if message.Header.Dst == self.name:
                    path_dbg |= 0x00000004
                    try:
                        self.channel_readings_received(from_node, message.Payload)
                    except Exception as e:
                        self.logger.error(f"problem with channel_readings_received: \n {e}")
                        return
                else:
                    path_dbg |= 0x00000008
                    try:
                        self.get_communicator(message.Header.Dst).process_message(message)
                    except Exception as e:
                        self.logger.error(f"problem with {message}: \n{e}")
            case FsmAtomicReport():
                path_dbg |= 0x00000010
                self.get_communicator(message.Header.Dst).process_message(message)
            case FsmEvent():
                path_dbg |= 0x00000020
                self.get_communicator(message.Header.Dst).process_message(message)
            case FsmFullReport():
                path_dbg |= 0x00000040
                if message.Header.Dst == self.name:
                    path_dbg |= 0x00000080
                    self.fsm_full_report_received(message.Payload)
                else:
                    path_dbg |= 0x00000100
                    self.get_communicator(message.Header.Dst).process_message(message)
            case MachineStates():
                path_dbg |= 0x00000200
                self.machine_states_received(message.Payload)
            case MicroVolts():
                path_dbg |= 0x00000400
                self.get_communicator(message.Header.Dst).process_message(message)
            case PicoMissing():
                path_dbg |= 0x00000800
                self.get_communicator(message.Header.Dst).process_message(message)
            case SingleReading():
                path_dbg |= 0x00001000
                self.single_reading_received(message.Payload)
            case SyncedReadings():
                if message.Header.Dst == self.name:
                    path_dbg |= 0x00002000
                    self.synced_readings_received(
                            from_node, message.Payload
                        )
                else:
                    path_dbg |=  0x00004000
                    try:
                        self.get_communicator(message.Header.Dst).process_message(message)
                    except Exception as e:
                        self.logger.error(f"problem with {message}: \n{e}")
            case TicklistHall():
                path_dbg |= 0x00008000
                self.get_communicator(message.Header.Dst).process_message(message)
            case TicklistHallReport():
                path_dbg |= 0x00010000
                self._links.publish_upstream(message.Payload, QOS.AtMostOnce)
            case TicklistReed():
                path_dbg |= 0x00020000
                self.get_communicator(message.Header.Dst).process_message(message)
            case TicklistReedReport():
                path_dbg |= 0x00040000
                self._links.publish_upstream(message.Payload, QOS.AtMostOnce)
            case _:
                raise ValueError(
                    f"There is no handler for message payload type [{type(message.Payload)}]"
                )
        self._logger.path("--Scada._derived_process_message  path:0x%08X", path_dbg)

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Message[Any]
    ) -> None:
        self._logger.path("++Scada._derived_process_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        if message.Payload.client_name == self.LOCAL_MQTT:
            path_dbg |= 0x00000001
            self._process_downstream_mqtt_message(message, decoded)
        elif message.Payload.client_name == self.GRIDWORKS_MQTT:
            path_dbg |= 0x00000002
            self._process_upstream_mqtt_message(message, decoded)
        elif message.Payload.client_name == self.ADMIN_MQTT:
            path_dbg |= 0x00000004
            self._process_admin_mqtt_message(message, decoded)
        else:
            raise ValueError("ERROR. No mqtt handler for mqtt client %s", message.Payload.client_name)
        self._logger.path("--Scada._derived_process_mqtt_message  path:0x%08X", path_dbg)

    def _process_upstream_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Message[Any]
    ) -> None:
        self._logger.path("++_process_upstream_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        match decoded.Payload:
            case AnalogDispatch():
                path_dbg |= 0x00000001
                self._analog_dispatch_received(decoded.Payload)
            case SendLayout():
                path_dbg |= 0x00000002
                self._send_layout_received(decoded.Payload)
            case SendSnap():
                path_dbg |= 0x00000004
                self._send_snap_received(decoded.Payload)
            case ScadaParams():
                path_dbg |= 0x00000008
                self._scada_params_received(decoded.Payload)
            case _:
                # Intentionally ignore this for forward compatibility
                path_dbg |= 0x00000010
        self._logger.path("--_process_upstream_mqtt_message  path:0x%08X", path_dbg)

    def _process_downstream_mqtt_message(
            self, message: Message[MQTTReceiptPayload], decoded: Message[Any]
    ) -> None:
        self._logger.path("++_process_downstream_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        match decoded.Payload:
            case EventBase():
                path_dbg |= 0x00000001
                self.generate_event(decoded.Payload)
            case SyncedReadings():
                path_dbg |= 0x00000002
                try:
                    self.synced_readings_received(
                        self._layout.node(decoded.Header.Src),
                        decoded.Payload
                    )
                except Exception as e:
                    #TODO - consider sending an Alert or ProbemEvent
                    self.logger.error(f"Failed to process SyncedReading from scada2!: {e}")
            case _:
                # Intentionally ignore this for forward compatibility
                path_dbg |= 0x00000004
        self._logger.path("--_process_downstream_mqtt_message  path:0x%08X", path_dbg)

    def _process_admin_mqtt_message(
            self, message: Message[MQTTReceiptPayload], decoded: Message[Any]
    ) -> None:
        self._logger.path("++_process_admin_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        if self.settings.admin.enabled:
            path_dbg |= 0x00000001
            match decoded.Payload:
                case AdminWakesUp():
                    path_dbg |= 0x00000002
                    self.admin_wakes_up_received(decoded.Payload)
                case FsmEvent():
                    # send into the _derived_process_message
                    to_name = decoded.Payload.ToHandle.split('.')[-1]
                    self.send(
                        Message(
                            header=Header(
                                Src=H0N.admin,
                                Dst=to_name,
                                MessageType=decoded.Payload.TypeName,
                            ),
                            Payload=decoded.Payload
                        )
                    )
                    path_dbg |= 0x00000004
                case AdminCommandReadRelays():
                    path_dbg |= 0x00000008
                    self._links.publish_message(
                        self.ADMIN_MQTT,
                        Message(
                            Src=self.publication_name,
                            Payload=RelayStates()
                        ),
                    )
                
                case _:
                    # Intentionally ignore this for forward compatibility
                    path_dbg |= 0x00000004
        self._logger.path("--_process_admin_mqtt_message  path:0x%08X", path_dbg)

    def _fsm_event_from_admin(self, fsm_event: FsmEvent) -> None:
        to_node = self._layout.node_from_handle(fsm_event.ToHandle)
        if to_node:
            self.get_communicator(to_node.name).process_message(fsm_event)
    
    def update_env_variable(self, variable, new_value) -> None:
        """
        Updates .env with new Scada Params. 
        TODO: move this somewhere else, like a local sqlite db
        """
        dotenv_filepath = dotenv.find_dotenv(usecwd=True)
        if not dotenv_filepath:
            self.logger.error("Couldn't find a .env file - perhaps because in CI?")
            return
        with open(dotenv_filepath, 'r') as file:
            lines = file.readlines()
        with open(dotenv_filepath, 'w') as file:
            line_exists = False
            for line in lines:
                if (line.startswith(f"{variable}=") 
                    or line.startswith(f"{variable}= ")
                    or line.startswith(f"{variable} =")
                    or line.startswith(f"{variable} = ")):
                    file.write(f"{variable}={new_value}\n")
                    line_exists = True      
                else:
                    file.write(line)
            if not line_exists:
                file.write(f"\n{variable}={new_value}\n")

    def _scada_params_received(self, message: ScadaParams) -> None:
        if message.FromGNodeAlias != self.hardware_layout.atn_g_node_alias:
            return
        new = message.NewParams
        if new:
            old = self.data.ha1_params
            self.data.ha1_params = new
            if new.AlphaTimes10 != old.AlphaTimes10:          
                self.update_env_variable('SCADA_ALPHA', new.AlphaTimes10 / 10)
            if new.BetaTimes100 != old.BetaTimes100:
                self.update_env_variable('SCADA_BETA', new.BetaTimes100 / 100)
            if new.GammaEx6 != old.GammaEx6:
                self.update_env_variable('SCADA_GAMMA', new.GammaEx6 / 1e6)
            if new.IntermediatePowerKw != old.IntermediatePowerKw:
                self.update_env_variable('SCADA_INTERMEDIATE_POWER', new.IntermediatePowerKw)
            if new.IntermediateRswtF != old.IntermediateRswtF:
                self.update_env_variable('SCADA_INTERMEDIATE_RSWT', new.IntermediateRswtF)
            if new.DdPowerKw != old.DdPowerKw:
                self.update_env_variable('SCADA_DD_POWER', new.DdPowerKw)
            if new.DdRswtF != old.DdRswtF:
                self.update_env_variable('SCADA_DD_RSWT', new.DdRswtF)
            if new.DdDeltaTF != old.DdDeltaTF:
                self.update_env_variable('SCADA_DD_DELTA_T', new.DdDeltaTF)

            response = ScadaParams(
                    FromGNodeAlias=self.hardware_layout.scada_g_node_alias,
                    FromName=self.name,
                    ToName=message.FromName,
                    UnixTimeMs=int(time.time() * 1000),
                    MessageId=message.MessageId,
                    NewParams=self.data.ha1_params,
                    OldParams=old,
                )
            self.logger.error(f"Sending back {response}")
            self._links.publish_upstream(response)
    
    def _send_layout_received(self, payload: SendLayout) -> None:
        print(f"Got SendLayout! {payload}")
        self.payload = payload
        if payload.FromGNodeAlias != self._layout.atn_g_node_alias:
            print(f"Not the correct gnode: {payload.FromGNodeAlias}")
            return
        if payload.FromName == H0N.atn:
            print("Sending layout info")
            self.send_layout_info()

    def _send_snap_received(self, payload: SendSnap):
        if payload.FromGNodeAlias != self._layout.atn_g_node_alias:
            return
        self._links.publish_upstream(self._data.make_snapshot())

    def power_watts_received(self, payload: PowerWatts):
        """The highest priority of the SCADA, from the perspective of the electric grid,
        is to report power changes as quickly as possible (i.e. milliseconds matter) on
        any asynchronous change more than x% (probably 2%).

        There is a single meter measuring all power getting reported - this is in fact
        what is Atomic (i.e. cannot be divided further) about the AtomicTNode. The
        asynchronous change calculation is already made in the power meter code. This
        function just passes through the result.

        The allocation to separate metered nodes is done ex-poste using the multipurpose
        telemetry data."""

        self._links.publish_upstream(payload, QOS.AtMostOnce)
        self._data.latest_total_power_w = payload.Watts
    
    def machine_states_received(self, payload: MachineStates) -> None:
        if payload.MachineHandle in self._data.recent_machine_states:
            prev: MachineStates = self._data.recent_machine_states[payload.MachineHandle]
            if payload.StateEnum != prev.StateEnum:
                raise Exception(f"{payload.MachineHandle} has conflicting state machines!"
                                f"{payload.StateEnum} and {prev.StateEnum}")
            
            self._data.recent_machine_states[payload.MachineHandle] =  MachineStates(
                MachineHandle=payload.MachineHandle,
                StateEnum=payload.StateEnum,
                UnixMsList=prev.UnixMsList + payload.UnixMsList,
                StateList=prev.StateList + payload.StateList,
            )
        else:
            self._data.recent_machine_states[payload.MachineHandle] = payload
            
    def fsm_full_report_received(self, payload: FsmFullReport) -> None:
        self._data.recent_fsm_reports[payload.TriggerId] = payload

    def single_reading_received(self, payload: SingleReading) -> None:
        if payload.ChannelName in self._layout.data_channels:
            ch = self._layout.data_channels[payload.ChannelName]
        elif payload.ChannelName in self._layout.synth_channels:
            ch = self._layout.synth_channels[payload.ChannelName]
        self._data.recent_channel_values[ch.Name].append(payload.Value)
        self._data.recent_channel_unix_ms[ch.Name].append(payload.ScadaReadTimeUnixMs)
        self._data.latest_channel_values[ch.Name] = payload.Value
        self._data.latest_channel_unix_ms[ch.Name] = payload.ScadaReadTimeUnixMs

    def synced_readings_received(
        self, from_node: ShNode, payload: SyncedReadings
    ):
        self._logger.path(
            "++synced_readings_received from: %s  channels: %d",
            from_node.Name,
            len(payload.ChannelNameList)
        )
        path_dbg = 0
        for idx, channel_name in enumerate(payload.ChannelNameList):
            path_dbg |= 0x00000001
            if channel_name not in self._layout.data_channels:
                raise ValueError(
                    f"Name {channel_name} in payload.SyncedReadings not a recognized Data Channel!"
                )
            ch = self._layout.data_channels[channel_name]
            self._data.recent_channel_values[ch.Name].append(
                payload.ValueList[idx]
            )
            self._data.recent_channel_unix_ms[
                ch.Name
            ].append(payload.ScadaReadTimeUnixMs)
            self._data.latest_channel_values[ch.Name] = payload.ValueList[idx]
            self._data.latest_channel_unix_ms[ch.Name] = payload.ScadaReadTimeUnixMs
        self._logger.path(
            "--gt_sh_telemetry_from_multipurpose_sensor_received  path:0x%08X", path_dbg
        )
    
    def channel_readings_received(
            self, from_node: ShNode, payload: ChannelReadings
    ) -> None:
        self._logger.path(
            "++channel_readings_received for channel: %d",
            payload.ChannelName
        )
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
            self._data.latest_channel_unix_ms[ch.Name] = payload.ScadaReadTimeUnixMsList[-1]

    def _send_to(self, dst: ShNode, payload: Any) -> None:
        message = Message(Src=self.name, Dst=dst.name,Payload=payload)
        if dst.name in set(self._communicators.keys()) | {self.name}:
            self.send(message)
        elif dst.Name == H0N.admin:
            self._links.publish_message(self.ADMIN_MQTT, message)
        elif dst.Name == H0N.atn:
            self._links.publish_upstream(payload)
        else:
            self._links.publish_message(self.LOCAL_MQTT, message)
          
    def run_in_thread(self, daemon: bool = True) -> threading.Thread:
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
    # State Machine related
    #####################################################################


    def _derived_recv_deactivated(self, transition: LinkManagerTransition) -> Result[bool, BaseException]:
        if transition.link_name == self.upstream_client:
            self._dispatch_live_hack = False
            self.logger.error("Link state: "
                              f" {self._links._states._links['gridworks'].curr_state.name.value}")
        return Ok()

    def _derived_recv_activated(self, transition: Transition) -> Result[bool, BaseException]:
        if transition.link_name == self.upstream_client:
            self._dispatch_live_hack = True
            self.logger.error("Link state: "
                              f" {self._links._states._links['gridworks'].curr_state.name.value}")
            
            self.send_layout_info()

        return Ok()

    def _analog_dispatch_received(self, dispatch: AnalogDispatch) -> None:
        self.logger.error("Got Analog Dispatch in SCADA!")
        if dispatch.FromGNodeAlias != self._layout.atn_g_node_alias:
            self.logger.error("IGNORING DISPATCH - NOT FROM MY ATN")
            return
        to_node = self.layout.node_by_handle(dispatch.ToHandle)
        if to_node:
            self.get_communicator(to_node.name).process_message(dispatch)
        # if self.top_state == TopState.Admin:
        #     to_node = self.layout.node_by_handle(dispatch.ToHandle)
        #     if to_node:
        #         self.get_communicator(to_node.name).process_message(dispatch)
        # elif self.top_state == TopState.Auto:
        #     self.pending_dispatch = dispatch
        #     # AdminWakesUp: Auto -> ChangingToAdmin
        #     self.AdminWakesUp()

        #     for node in self.layout.direct_reports(self.auto_node):
        #         self._send_to(node, GoDormant(
        #             FromName=H0N.auto, 
        #             ToName=node.name,
        #             TriggerId=dispatch.TriggerId))
        # #TODO: if MainAutoState is not atn, ignore
    
    def dormant_received(self, ack: DormantAck) -> None:
        if ack.ToName == H0N.auto:
            direct_report = self.layout.node(ack.FromName)
            

    def admin_wakes_up_received(self, wakeup: AdminWakesUp) -> None:
        if wakeup.FromName != H0N.admin:
            raise Exception(f"Expect admin wakes up from {H0N.admin}, got {wakeup.FromName}")
        if self.top_state != TopState.Auto:
            self.logger.error(f"Ignoring admin wakeup, in state {self.top_state}")
            return

        # AdminWakesUp: Auto -> ChangingToAdmin
        self.AdminWakesUp()

        for node in self.layout.direct_reports(self.auto_node):
            self._send_to(node, GoDormant(FromName=H0N.auto, ToName=node.name))

        #TODO: turn this into a recursion where reports hand over THEIR reports to their boss
        # and then as a final step go dormant.

        # hack for now:
        # 1. auto FSM (and all sub-fsms, e.g. HomeAlone) goes dormant
        if self.auto_state != MainAutoState.Dormant:
            self.GoDormant()

        # 2. Make admin the direct boss of all relays and dfrs
        relay_nodes = [node for node in self._layout.nodes.values() if node.ActorClass == ActorClass.Relay] 
        dfr_nodes = [node for node in self._layout.nodes.values() if node.ActorClass == ActorClass.ZeroTenOutputer] 

        for node in relay_nodes + dfr_nodes:
            node.Handle = f"{H0N.admin}.{node.Name}"
        
        self.logger.warning("All relays and dfrs now have admin as boss")
        time.sleep(0.5)

        # AdminWakesUp: ChangingToAdmin -> Admin
        self.trigger(TopEvent.ChangeToAdmin)
        message = Message(
            Src=self.name, 
            Dst=H0N.admin, 
            Payload=AdminWakesUp(FromName=self.name, ToName=H0N.admin)
        )
        return self.services._links.publish_message(
                self.services.ADMIN_MQTT, message, qos=QOS.AtMostOnce
            )

    async def state_tracker(self) -> None:
        loop_s = self.settings.seconds_per_report
        while True:
            hiccup = 1.5
            sleep_s = max(
                hiccup, loop_s - (time.time() % loop_s) - 1.2
            )
            await asyncio.sleep(sleep_s)
            # report the state
            if sleep_s != hiccup:
                self.machine_states_received(
                    MachineStates(
                        MachineHandle=self.node.handle,
                        StateEnum=TopState.enum_name(),
                        StateList=[self.top_state],
                        UnixMsList=[int(time.time() * 1000)],
                    ),
                )

                self.machine_states_received(
                    MachineStates(
                        MachineHandle=self.auto_node.handle,
                        StateEnum=MainAutoState.enum_name(),
                        StateList=[self.auto_state],
                        UnixMsList=[int(time.time() * 1000)],
                    ),
                )
                self.logger.warning(f"Top state: {self.top_state}")
                self.logger.warning(f"Auto state: {self.auto_state}")

    @property
    def slow_dispatch_live(self):
        """
        ORIGINAL VISION (aka WHAT I WOULD HAVE GIVEN MY EYE TEETH
        FOR BACK AT VCHARGE)

         False if:
           - interactive polling between atn and scada is down [TESTING]
           - Scada sends notification that it is switching to home alone, and
           received an application-level (as opposed to say broker-level) ack
           - Atn requests that Scada take local control and Scada has agreed
           - scada sends "turn on" and power is not at 80% of max within 5 minutes
             and/or total charge for the market slot is not within 10% of projected
           - Fast more like:
                - scada sent dispatch command with more than 6 seconds; and
             before response as measured by power meter (requires a lot of clarification)
                -average time for response to dispatch commands in last 50 dispatches
             exceeds 3 seconds
           - Scada has not sent in daily attestion that power metering is
             working and accurate
           - no contract exists [i.e. ]


           Otherwise True

           Note that typically, the contract will not be alive because of house to
           cloud comms failure. But not always. There will be significant and important
           times (like when testing home alone perforamance) where we will want to send
           status messages etc up to the cloud even when the dispatch contract is not
           alive.
        """
        if self.auto_state == "Atn":
            if not self._dispatch_live_hack:
                raise Exception("WTF. _dispatch_live_hack False but auto_state is Atn ")
            return True
        else:
            if self._dispatch_live_hack:
                raise Exception(f"WTF. _dispatch_live_hack True but auto_state is {self._auto_state}")
            return False
            
