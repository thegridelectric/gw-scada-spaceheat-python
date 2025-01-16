"""Parentless (Scada2) implementation"""
import importlib
import asyncio
import threading
from typing import Any, Optional
from typing import List

from gwproactor.external_watchdog import SystemDWatchdogCommandBuilder
from gwproactor.persister import TimedRollingFilePersister
from gwproto.message import Header
from gwproactor.links.link_settings import LinkSettings
from gwproto.message import Message
from gwproto.named_types import PowerWatts, Report, SyncedReadings
from gwproto.named_types import SnapshotSpaceheat
from data_classes.house_0_names import H0N
from data_classes.house_0_layout import House0Layout
from gwproto.data_classes.sh_node import ShNode

from actors.scada_interface import ScadaInterface
from actors.config import ScadaSettings
from gwproactor import QOS
from gwproactor import ActorInterface
from gwproactor.message import MQTTReceiptPayload
from gwproactor.proactor_implementation import Proactor
from actors.scada import (
    LocalMQTTCodec,
)

class Scada2Data:
    latest_snap: Optional[SnapshotSpaceheat]
    latest_report: Optional[Report]
    def __init__(self) -> None:
        self.latest_snap = None
        self.latest_report = None

class Parentless(ScadaInterface, Proactor):
    ASYNC_POWER_REPORT_THRESHOLD = 0.05
    DEFAULT_ACTORS_MODULE = "actors"
    LOCAL_MQTT = "local"
    _data: Scada2Data

    def __init__(
        self,
        name: str,
        settings: ScadaSettings,
        hardware_layout: House0Layout,
        actors_package_name: Optional[str] = None
    ):
        if type(hardware_layout) is not House0Layout:
            raise Exception(f"hardware_layout is of type {type(hardware_layout)}!!")
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        self._links.add_mqtt_link(
            LinkSettings(
                client_name=Parentless.LOCAL_MQTT,
                gnode_name=self._layout.scada_g_node_alias,
                spaceheat_name=H0N.primary_scada,
                mqtt=self.settings.local_mqtt,
                codec=LocalMQTTCodec(
                    primary_scada=False,
                    remote_node_names=set([self._layout.scada_g_node_alias.replace(".", "-")]),
                ),
                upstream=True,
            )
        )
        self._layout: House0Layout = hardware_layout
        self._links.log_subscriptions("construction")
        self._data = Scada2Data()
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

    @classmethod
    def make_event_persister(cls, settings: ScadaSettings) -> TimedRollingFilePersister:
        return TimedRollingFilePersister(
            settings.paths.event_dir,
            max_bytes=settings.persister.max_bytes,
            pat_watchdog_args=SystemDWatchdogCommandBuilder.pat_args(
                str(settings.paths.name)
            ),
        )

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

    @property
    def name(self):
        return self._name

    @property
    def subscription_name(self) -> str:
        return H0N.secondary_scada

    @property
    def node(self) -> ShNode:
        return self._node

    @property
    def settings(self):
        return self._settings

    @property
    def data(self) -> Scada2Data:
        return self._data  
 
    @property
    def hardware_layout(self) -> House0Layout:
        return self._layout

    def _publish_to_local(self, from_node: ShNode, payload, qos: QOS = QOS.AtMostOnce):
        message = Message(Src=from_node.Name, Payload=payload)
        return self._links.publish_message(Parentless.LOCAL_MQTT, message, qos=qos)

    def _derived_process_message(self, message: Message):
        self._logger.path("++Parentless._derived_process_message %s/%s", message.Header.Src, message.Header.MessageType)
        path_dbg = 0
        match message.Payload:
            case PowerWatts():
                new_msg = Message(
                    Header=Header(
                        Src=message.Header.Src, 
                        Dst=H0N.primary_scada,
                        MessageType=message.Payload.TypeName,
                        ),
                    Payload=message.Payload
                )
                self._links.publish_message(Parentless.LOCAL_MQTT, new_msg, QOS.AtMostOnce)
            case SyncedReadings():
                path_dbg |= 0x00000004
                new_msg = Message(
                    Header=Header(
                        Src=message.Header.Src, 
                        Dst=H0N.primary_scada,
                        MessageType=message.Payload.TypeName,
                        ),
                    Payload=message.Payload
                )
                self._links.publish_message(Parentless.LOCAL_MQTT, new_msg, QOS.AtMostOnce)
            case _:
                raise ValueError(
                    f"There is no handler for message payload type [{type(message.Payload)}]"
                )
        self._logger.path("--Parentless._derived_process_message  path:0x%08X", path_dbg)

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        self._logger.path("++Parentless._derived_process_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        match decoded.Payload:
            case Report():
                path_dbg |= 0x00000001
                self.report_received(decoded.Payload)
            case SnapshotSpaceheat():
                path_dbg |= 0x00000002
                self.snapshot_received(decoded.Payload)
            case _:
                # Intentionally ignored for forward compatibility
                path_dbg |= 0x00000004
        self._logger.path("--Parentless._derived_process_mqtt_message  path:0x%08X", path_dbg)

    def snapshot_received(self, payload: SnapshotSpaceheat)-> None:
        self._data.latest_snap = payload

    def report_received(self, payload: Report)-> None:
        self._data.latest_report = payload
    
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
