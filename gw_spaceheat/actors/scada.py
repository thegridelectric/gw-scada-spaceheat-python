"""Scada implementation"""

import asyncio
import enum
import threading
import time
from typing import Any
from typing import List
from typing import Optional

from gwproactor.external_watchdog import SystemDWatchdogCommandBuilder
from gwproactor.links import LinkManagerTransition
from gwproactor.message import InternalShutdownMessage
from gwproto import Message
from gwproto import create_message_model
from gwproto.messages import PowerWatts
from gwproto.messages import GtShCliAtnCmd
from gwproto.messages import GtShStatusEvent
from gwproto.messages import GtShTelemetryFromMultipurposeSensor
from gwproto import MQTTCodec
from gwproto import MQTTTopic
from gwproto.messages import SnapshotSpaceheatEvent
from result import Ok
from result import Result

from actors.home_alone import HomeAlone
from gwproactor import ActorInterface
from actors.scada_data import ScadaData
from actors.scada_interface import ScadaInterface
from actors.config import ScadaSettings
from gwproto.data_classes.hardware_layout import HardwareLayout
from gwproto.data_classes.sh_node import ShNode
from gwproto.data_classes.telemetry_tuple import TelemetryTuple
from gwproactor import QOS
from gwproactor.links import Transition
from gwproactor.message import MQTTReceiptPayload
from gwproactor.persister import TimedRollingFilePersister
from gwproactor.proactor_implementation import Proactor

ScadaMessageDecoder = create_message_model(
    "ScadaMessageDecoder",
    [
        "gwproto.messages",
        "gwproactor.message",
        "actors.message"
    ]
)


class GridworksMQTTCodec(MQTTCodec):
    hardware_layout: HardwareLayout

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(ScadaMessageDecoder)

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.atn_g_node_alias:
            raise Exception(
                f"alias {source_alias} not my AtomicTNode ({self.hardware_layout.atn_g_node_alias})!"
            )


class LocalMQTTCodec(MQTTCodec):

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(ScadaMessageDecoder)

    def validate_source_alias(self, source_alias: str):
        if source_alias not in self.hardware_layout.nodes.keys():
            raise Exception(f"{source_alias} not a node name!")

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
    GRIDWORKS_MQTT = "gridworks"
    LOCAL_MQTT = "local"

    _data: ScadaData
    _last_status_second: int
    _scada_atn_fast_dispatch_contract_is_alive_stub: bool
    _home_alone: HomeAlone

    def __init__(
        self,
        name: str,
        settings: ScadaSettings,
        hardware_layout: HardwareLayout,
        actor_nodes: Optional[List[ShNode]] = None,
    ):
        self._data = ScadaData(settings, hardware_layout)
        super().__init__(name=name, settings=settings, hardware_layout=hardware_layout)
        self._links.add_mqtt_link(
            Scada.LOCAL_MQTT, self.settings.local_mqtt, LocalMQTTCodec(self._layout)
        )
        self._links.add_mqtt_link(
            Scada.GRIDWORKS_MQTT,
            self.settings.gridworks_mqtt,
            GridworksMQTTCodec(self._layout),
            upstream=True,
            primary_peer=True,
        )
        topic = MQTTTopic.encode_subscription(Message.type_name(), self._layout.atn_g_node_alias)

        self._links.subscribe(Scada.GRIDWORKS_MQTT, topic, QOS.AtMostOnce)
        # TODO: clean this up
        self._links.log_subscriptions("construction")
        # self._home_alone = HomeAlone(H0N.home_alone, self)
        # self.add_communicator(self._home_alone)
        now = int(time.time())
        self._last_status_second = int(now - (now % self.settings.seconds_per_report))
        self._scada_atn_fast_dispatch_contract_is_alive_stub = False
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
            asyncio.create_task(self.update_status(), name="update_status")
        )

    async def update_status(self):
        while not self._stop_requested:
            try:
                if self.time_to_send_status():
                    self.send_status()
                    self._last_status_second = int(time.time())
                await asyncio.sleep(self.seconds_until_next_status())
            except Exception as e:
                try:
                    if not isinstance(e, asyncio.CancelledError):
                        self._logger.exception(e)
                        self._send(
                            InternalShutdownMessage(
                                Src=self.name,
                                Reason=(
                                    f"update_status() task got exception: <{type(e)}> {e}"
                                ),
                            )
                        )
                finally:
                    break


    def send_status(self):
        status = self._data.make_status(self._last_status_second)
        self._data.status_to_store[status.StatusUid] = status
        self.generate_event(GtShStatusEvent(status=status))
        snapshot = self._data.make_snapshot()
        self._publish_to_local(self._node, status)
        self._publish_to_local(self._node, snapshot)
        self.generate_event(SnapshotSpaceheatEvent(snap=snapshot))
        # try:
        #     self._home_alone.process_message(Message(Src=self.name, Payload=snapshot))
        # except BaseException as e:
        #     self._logger.exception(e)
        #     raise e
        self._data.flush_latest_readings()

    def next_status_second(self) -> int:
        last_status_second_nominal = int(
            self._last_status_second
            - (self._last_status_second % self.settings.seconds_per_report)
        )
        return last_status_second_nominal + self.settings.seconds_per_report

    def seconds_until_next_status(self) -> float:
        return self.next_status_second() - time.time()

    def time_to_send_status(self) -> bool:
        return time.time() > self.next_status_second()

    def _derived_recv_deactivated(self, transition: LinkManagerTransition) -> Result[bool, BaseException]:
        self._scada_atn_fast_dispatch_contract_is_alive_stub = False
        return Ok()

    def _derived_recv_activated(self, transition: Transition) -> Result[bool, BaseException]:
        self._scada_atn_fast_dispatch_contract_is_alive_stub = True
        return Ok()

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
            case GtShTelemetryFromMultipurposeSensor():
                path_dbg |= 0x00000040
                self.gt_sh_telemetry_from_multipurpose_sensor_received(
                        from_node, message.Payload
                    )
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


    # def _boolean_dispatch_received(
    #     self, payload: GtDispatchBoolean
    # ) -> ScadaCmdDiagnostic:
    #     """This is a dispatch message received from the atn. It is
    #     honored whenever DispatchContract with the Atn is live."""
    #     if not self.scada_atn_fast_dispatch_contract_is_alive:
    #         return ScadaCmdDiagnostic.IGNORING_ATN_DISPATCH
    #     return self._process_boolean_dispatch(payload)

    # def _process_boolean_dispatch(
    #     self, payload: GtDispatchBoolean
    # ) -> ScadaCmdDiagnostic:
    #     ba = self._layout.node(payload.AboutNodeName)
    #     if not isinstance(ba.component, RelayComponent):
    #         return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_RELAY
    #     self._communicators[ba.alias].process_message(
    #         GtDispatchBooleanLocalMessage(
    #             src=self.name, dst=ba.alias, relay_state=payload.RelayState
    #         )
    #     )
    #     return ScadaCmdDiagnostic.SUCCESS

    # def _set_relay_state_threadsafe(self, ba: ShNode, on: bool):
    #     if not isinstance(ba.component, RelayComponent):
    #         return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_RELAY
    #     self.send_threadsafe(
    #         GtDispatchBooleanLocalMessage(
    #             src=self._layout.home_alone_node.alias, dst=ba.alias, relay_state=on
    #         )
    #     )
    #     return ScadaCmdDiagnostic.SUCCESS

    # def turn_on(self, ba: ShNode) -> ScadaCmdDiagnostic:
    #     return self._set_relay_state_threadsafe(ba, True)

    # def turn_off(self, ba: ShNode) -> ScadaCmdDiagnostic:
    #     return self._set_relay_state_threadsafe(ba, False)

    def _gt_sh_cli_atn_cmd_received(self, payload: GtShCliAtnCmd):
        if payload.SendSnapshot is not True:
            return
        self._links.publish_upstream(self._data.make_snaphsot_payload())

    @property
    def scada_atn_fast_dispatch_contract_is_alive(self):
        """
        TO IMPLEMENT:

         False if:
           - no contract exists
           - interactive polling between atn and scada is down
           - scada sent dispatch command with more than 6 seconds before response
             as measured by power meter (requires a lot of clarification)
           - average time for response to dispatch commands in last 50 dispatches
             exceeds 3 seconds
           - Scada has not sent in daily attestion that power metering is
             working and accurate
           - Scada requests local control and Atn has agreed
           - Atn requests that Scada take local control and Scada has agreed
           - Scada has not sent in an attestion that metering is good in the
             previous 24 hours

           Otherwise true

           Note that typically, the contract will not be alive because of house to
           cloud comms failure. But not always. There will be significant and important
           times (like when testing home alone perforamance) where we will want to send
           status messages etc up to the cloud even when the dispatch contract is not
           alive.
        """
        return self._scada_atn_fast_dispatch_contract_is_alive_stub

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

    def gt_sh_telemetry_from_multipurpose_sensor_received(
        self, from_node: ShNode, payload: GtShTelemetryFromMultipurposeSensor
    ):
        self._logger.path(
            "++gt_sh_telemetry_from_multipurpose_sensor_received from: %s  nodes: %d",
            from_node.Name,
            len(payload.AboutNodeAliasList)
        )
        path_dbg = 0
        for idx, about_name in enumerate(payload.AboutNodeAliasList):
            path_dbg |= 0x00000001
            if about_name not in self._layout.nodes:
                raise Exception(
                    f"Name {about_name} in payload.AboutNodeAliasList not a recognized ShNode!"
                )
            tt = TelemetryTuple(
                AboutNode=self._layout.node(about_name),
                SensorNode=from_node,
                TelemetryName=payload.TelemetryNameList[idx],
            )
            if tt not in self._layout.my_telemetry_tuples:
                raise Exception(f"Scada not tracking telemetry tuple {tt}!")
            self._data.recent_values_from_multipurpose_sensor[tt].append(
                payload.ValueList[idx]
            )
            self._data.recent_read_times_unix_ms_from_multipurpose_sensor[
                tt
            ].append(payload.ScadaReadTimeUnixMs)
            self._data.latest_value_from_multipurpose_sensor[
                tt
            ] = payload.ValueList[idx]
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
