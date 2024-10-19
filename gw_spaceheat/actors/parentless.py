"""Parentless (Scada2) implementation"""
import importlib
import asyncio
import threading
import time
from typing import Any, Optional
from typing import List

from gwproactor.external_watchdog import SystemDWatchdogCommandBuilder
from gwproactor.links import LinkManagerTransition
from gwproactor.message import InternalShutdownMessage
from gwproto.message import Message
from gwproto.messages import PowerWatts
from gwproto.messages import GtShCliAtnCmd
from gwproto.messages import ReportEvent
from gwproto.messages import SyncedReadings
from gwproto import MQTTTopic
from result import Ok
from result import Result

from gwproactor import ActorInterface

from actors.api_tank_module import MicroVolts
from actors.scada_data import ScadaData
from actors.scada_interface import ScadaInterface
from actors.config import ScadaSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.sh_node import ShNode
from gwproactor import QOS
from gwproactor.links import Transition
from gwproactor.message import MQTTReceiptPayload
from gwproactor.persister import TimedRollingFilePersister
from gwproactor.proactor_implementation import Proactor
from actors.scada import (
    SYNC_SNAP_S, 
    GridworksMQTTCodec,
)


class Parentless(ScadaInterface, Proactor):
    ASYNC_POWER_REPORT_THRESHOLD = 0.05
    DEFAULT_ACTORS_MODULE = "actors"
    GRIDWORKS_MQTT = "gridworks"
    LOCAL_MQTT = "local"

    _data: ScadaData
    _last_report_second: int
    _last_sync_snap_s: int
    _scada_atn_fast_dispatch_contract_is_alive_stub: bool
    #_home_alone: HomeAlone
    _channels_reported: bool

    def __init__(
        self,
        name: str,
        settings: ScadaSettings,
        hardware_layout: HardwareLayout,
        actors_package_name: Optional[str] = None
    ):
        self._data = ScadaData(settings, hardware_layout)
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        # self._links.add_mqtt_link(
        #     Scada.LOCAL_MQTT, self.settings.local_mqtt, LocalMQTTCodec(self._layout)
        # )
        self._links.add_mqtt_link(
            Parentless.GRIDWORKS_MQTT,
            self.settings.gridworks_mqtt,
            GridworksMQTTCodec(self._layout),
            upstream=True,
            primary_peer=True,
        )
        self._links.subscribe(
            Parentless.GRIDWORKS_MQTT,
            MQTTTopic.encode_subscription(Message.type_name(), self._layout.atn_g_node_alias),
            QOS.AtMostOnce
        )
        # FIXME: this causes tests to fail horrible ways.
        # self._links.subscribe(
        #     Scada2.LOCAL_MQTT,
        #     MQTTTopic.encode_subscription(Message.type_name(), self._layout.scada_g_node_alias),
        #     QOS.AtMostOnce
        # )

        self._links.log_subscriptions("construction")
        # self._home_alone = HomeAlone(H0N.home_alone, self)
        # self.add_communicator(self._home_alone)
        now = int(time.time())
        self._channels_reported = False
        self._last_report_second = int(now - (now % self.settings.seconds_per_report))
        self._last_sync_snap_s = int(now)
        self._scada_atn_fast_dispatch_contract_is_alive_stub = False
        
        self.actors_package_name = actors_package_name
        if actors_package_name is None:
            self.actors_package_name = self.DEFAULT_ACTORS_MODULE

        actor_nodes = self.get_actor_nodes()
        for actor_node in actor_nodes:
            self.add_communicator(
                ActorInterface.load(
                    actor_node.Name,
                    str(actor_node.actor_class),
                    self,                    self.DEFAULT_ACTORS_MODULE
                )
            )

    def init(self) -> None:
        """Called after constructor so derived functions can be used in setup."""
        print("hi!")
    
    def get_actor_nodes(self) -> List[ShNode]:
        actors_package = importlib.import_module(self.actors_package_name)
        actor_nodes = []
        my_kids = [node for node in self._layout.nodes.values() if 
                   self._layout.parent_node(node) == self._node and 
                   node != self._node and
                   node.has_actor]
        for node in my_kids:
            if not getattr(actors_package, node.actor_class):
                raise ValueError(
                    f"ERROR. Actor class {node.actor_class} for node {node.Name} "
                    f"not in actors package {self.actors_package_name}"
                )
            else:
                actor_nodes.append(node)
        return actor_nodes

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
    def settings(self):
        return self._settings

    @property
    def hardware_layout(self) -> HardwareLayout:
        return self._layout

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

    def send_report(self):
        report = self._data.make_report(self._last_report_second)
        self._links.publish_upstream(report)
        self._data.flush_latest_readings()
    
    def send_snap(self):
        snapshot = self._data.make_snapshot()
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

    def _derived_recv_deactivated(self, transition: LinkManagerTransition) -> Result[bool, BaseException]:
        self._scada_atn_fast_dispatch_contract_is_alive_stub = False
        return Ok()

    def _derived_recv_activated(self, transition: Transition) -> Result[bool, BaseException]:
        self._scada_atn_fast_dispatch_contract_is_alive_stub = True
        return Ok()

    def _publish_to_local(self, from_node: ShNode, payload, qos: QOS = QOS.AtMostOnce):
        message = Message(Src=from_node.Name, Payload=payload)
        return self._links.publish_message(Parentless.LOCAL_MQTT, message, qos=qos)

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
            case SyncedReadings():
                path_dbg |= 0x00000040
                self.synced_readings_received(
                        from_node, message.Payload
                    )
            case MicroVolts():
                self.get_communicator(message.Header.Dst).process_message(message)

            case _:
                raise ValueError(
                    f"There is no handler for mqtt message payload type [{type(message.Payload)}]"
                )
        self._logger.path("--Scada._derived_process_message  path:0x%08X", path_dbg)

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        self._logger.path("++Scada._derived_process_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        if message.Payload.client_name != self.GRIDWORKS_MQTT:
            raise ValueError(
                f"There are no messages expected to be received from [{message.Payload.client_name}] mqtt broker. "
                f"Received\n\t topic: [{message.Payload.message.topic}]"
            )
        match decoded.Payload:
            case GtShCliAtnCmd():
                path_dbg |= 0x00000002
                self._gt_sh_cli_atn_cmd_received(decoded.Payload)
            case _:
                raise ValueError(
                    f"There is no handler for mqtt message payload type [{type(decoded.Payload)}]\n"
                    f"Received\n\t topic: [{message.Payload.message.topic}]"
                )
        self._logger.path("--Scada._derived_process_mqtt_message  path:0x%08X", path_dbg)

    def _gt_sh_cli_atn_cmd_received(self, payload: GtShCliAtnCmd):
        if payload.SendSnapshot is not True:
            return
        self._links.publish_upstream(self._data.make_snapshot())

    @property
    def scada_atn_fast_dispatch_contract_is_alive(self):
        return self._scada_atn_fast_dispatch_contract_is_alive_stub

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
            self._data.recent_channel_values[ch].append(
                payload.ValueList[idx]
            )
            self._data.recent_channel_unix_ms[
                ch
            ].append(payload.ScadaReadTimeUnixMs)
            self._data.latest_channel_values[ch] = payload.ValueList[idx]
            self._data.latest_channel_unix_ms[ch] = payload.ScadaReadTimeUnixMs
        self._logger.path(
            "--gt_sh_telemetry_from_multipurpose_sensor_received  path:0x%08X", path_dbg
        )

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
