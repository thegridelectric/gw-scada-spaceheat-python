"""Scada implementation"""

import asyncio
import json
import time
import typing
from typing import Any
from typing import List
from typing import Optional

from gwproto import Message
from gwproto import Decoders
from gwproto import create_message_payload_discriminator
from gwproto.messages import EventT
from gwproto.messages import GsPwr
from gwproto.messages import GtDispatchBoolean
from gwproto.messages import GtDispatchBoolean_Maker
from gwproto.messages import GtDispatchBooleanLocal
from gwproto.messages import GtDriverBooleanactuatorCmd
from gwproto.messages import GtDriverBooleanactuatorCmd_Maker
from gwproto.messages import GtShCliAtnCmd
from gwproto.messages import GtShCliAtnCmd_Maker
from gwproto.messages import GtShTelemetryFromMultipurposeSensor
from gwproto.messages import GtShTelemetryFromMultipurposeSensor_Maker
from gwproto.messages import GtTelemetry
from gwproto.messages import GtTelemetry_Maker
from gwproto import MQTTCodec
from gwproto import MQTTTopic
from paho.mqtt.client import MQTTMessageInfo
from result import Err
from result import Ok

from actors2.actor_interface import ActorInterface
from actors2.message import GtDispatchBooleanLocalMessage
from actors2.message import ScadaDBG
from actors2.message import ScadaDBGCommands
from actors2.message import ScadaDBGEvent
from actors2.scada_data import ScadaData
from actors2.scada_interface import ScadaInterface
from actors.scada import ScadaCmdDiagnostic
from actors.utils import QOS
from config import ScadaSettings
from data_classes.components.boolean_actuator_component import BooleanActuatorComponent
from data_classes.hardware_layout import HardwareLayout
from data_classes.sh_node import ShNode
from named_tuples.telemetry_tuple import TelemetryTuple
from proactor.logger import ProactorLogger
from proactor.message import MQTTReceiptPayload
from proactor.message import MQTTSubackPayload
from proactor.persister import TimedRollingFilePersister
from proactor.proactor_implementation import Proactor
from proactor.proactor_implementation import AckWaitResult

ScadaMessageDecoder = create_message_payload_discriminator(
    "ScadaMessageDecoder",
    [
        "gwproto.messages",
        "actors2.message"
    ]
)


class GridworksMQTTCodec(MQTTCodec):
    hardware_layout: HardwareLayout

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(
            Decoders.from_objects(
                [
                    GtDispatchBoolean_Maker,
                    GtShCliAtnCmd_Maker,
                ],
                message_payload_discriminator=ScadaMessageDecoder,
            )
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias != self.hardware_layout.atn_g_node_alias:
            raise Exception(
                f"alias {source_alias} not my AtomicTNode ({self.hardware_layout.atn_g_node_alias})!"
            )


class LocalMQTTCodec(MQTTCodec):

    def __init__(self, hardware_layout: HardwareLayout):
        self.hardware_layout = hardware_layout
        super().__init__(
            Decoders.from_objects(
                [
                    GtDriverBooleanactuatorCmd_Maker,
                    GtShTelemetryFromMultipurposeSensor_Maker,
                    GtTelemetry_Maker,
                ],
                message_payload_discriminator=ScadaMessageDecoder,
            )
        )

    def validate_source_alias(self, source_alias: str):
        if source_alias not in self.hardware_layout.nodes.keys():
            raise Exception(f"alias {source_alias} not in ShNode.by_alias keys!")


class Scada2(ScadaInterface, Proactor):
    GS_PWR_MULTIPLIER = 1
    ASYNC_POWER_REPORT_THRESHOLD = 0.05
    DEFAULT_ACTORS_MODULE = "actors2"
    GRIDWORKS_MQTT = "gridworks"
    LOCAL_MQTT = "local"

    _settings: ScadaSettings
    _nodes: HardwareLayout
    _node: ShNode
    _data: ScadaData
    _event_persister: TimedRollingFilePersister
    _last_status_second: int
    _scada_atn_fast_dispatch_contract_is_alive_stub: bool

    def __init__(
        self,
        name: str,
        settings: ScadaSettings,
        hardware_layout: HardwareLayout,
        actor_nodes: Optional[List[ShNode]] = None,
    ):
        super().__init__(
            name=name,
            logger=ProactorLogger(**settings.logging.qualified_logger_names())
        )
        self._node = hardware_layout.node(name)
        self._settings = settings
        self._layout = hardware_layout
        self._data = ScadaData(settings, hardware_layout)
        self._add_mqtt_client(
            Scada2.LOCAL_MQTT, self.settings.local_mqtt, LocalMQTTCodec(self._layout)
        )
        self._add_mqtt_client(
            Scada2.GRIDWORKS_MQTT,
            self.settings.gridworks_mqtt,
            GridworksMQTTCodec(self._layout),
        )
        for topic in [
            MQTTTopic.encode_subscription(self._layout.atn_g_node_alias, Message.type_name()),
            f"{self._layout.atn_g_node_alias}/{GtDispatchBoolean_Maker.type_alias}".replace(".", "-"),
            f"{self._layout.atn_g_node_alias}/{GtShCliAtnCmd_Maker.type_alias}".replace(".", "-"),
        ]:
            self._mqtt_clients.subscribe(Scada2.GRIDWORKS_MQTT, topic, QOS.AtMostOnce)
        # TODO: clean this up
        self.log_subscriptions("construction")
        now = int(time.time())
        self._last_status_second = int(now - (now % self.settings.seconds_per_report))
        self._scada_atn_fast_dispatch_contract_is_alive_stub = False
        self._event_persister = TimedRollingFilePersister(self.settings.paths.event_dir)
        if actor_nodes is not None:
            for actor_node in actor_nodes:
                self.add_communicator(
                    ActorInterface.load(
                        actor_node.alias,
                        actor_node.actor_class.value,
                        self,
                        self.DEFAULT_ACTORS_MODULE
                    )
                )

    @property
    def alias(self):
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

    def _start_derived_tasks(self):
        self._tasks.append(
            asyncio.create_task(self.update_status(), name="update_status")
        )

    async def update_status(self):
        while not self._stop_requested:
            if self.time_to_send_status() and self._link_states[Scada2.GRIDWORKS_MQTT].active_for_send():
                self.send_status()
                self._last_status_second = int(time.time())
            await asyncio.sleep(self.seconds_until_next_status())

    def send_status(self):
        status = self._data.make_status(self._last_status_second)
        self._data.status_to_store[status.StatusUid] = status
        self._publish_to_gridworks(status.asdict())
        self._publish_to_local(self._node, status)
        self._publish_to_gridworks(self._data.make_snaphsot_payload())
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

    def generate_event(self, event: EventT) -> None:
        if not event.Src:
            event.Src = self.publication_name
        self._publish_to_gridworks(event, AckRequired=True)
        self._event_persister.persist(event.MessageId, event.json(sort_keys=True, indent=2).encode("utf-8"))

    def _derived_process_ack_result(self, result: AckWaitResult):
        self._logger.path("++Scada2._derived_process_ack_result %s %s", result.wait_info.message_id, result.summary)
        path_dbg = 0
        if result.ok() and result.wait_info.message_id in self._event_persister:
            path_dbg |= 0x00000001
            self._event_persister.clear(result.wait_info.message_id)
        self._logger.path("--Scada2._derived_process_ack_result path:0x%08X", path_dbg)

    def _publish_to_gridworks(
        self, payload, qos: QOS = QOS.AtMostOnce, **message_args: Any
    ) -> MQTTMessageInfo:
        message = Message(Src=self.publication_name, Payload=payload, **message_args)
        return self._publish_message(Scada2.GRIDWORKS_MQTT, message, qos=qos)

    def _publish_to_local(self, from_node: ShNode, payload, qos: QOS = QOS.AtMostOnce):
        message = Message(Src=from_node.alias, Payload=payload)
        return self._publish_message(Scada2.LOCAL_MQTT, message, qos=qos)

    def _derived_process_message(self, message: Message):
        self._logger.path("++Scada2._derived_process_message %s/%s", message.Header.Src, message.Header.MessageType)
        path_dbg = 0
        from_node = self._layout.node(message.Header.Src, None)
        match message.Payload:
            case GsPwr():
                path_dbg |= 0x00000001
                if from_node is self._layout.power_meter_node:
                    path_dbg |= 0x00000002
                    self.gs_pwr_received(message.Payload)
                else:
                    raise Exception(
                        f"message.Header.Src {message.Header.Src} must be from {self._layout.power_meter_node} for GsPwr message"
                    )
            case GtDispatchBooleanLocal():
                path_dbg |= 0x00000004
                if message.Header.Src == "a.home":
                    path_dbg |= 0x00000008
                    self.local_boolean_dispatch_received(message.Payload)
                else:
                    raise Exception(
                        "message.Header.Src must be a.home for GsDispatchBooleanLocal message"
                    )
            case GtTelemetry():
                path_dbg |= 0x00000010
                if from_node in self._layout.my_simple_sensors:
                    path_dbg |= 0x00000020
                    self.gt_telemetry_received(from_node, message.Payload)
            case GtShTelemetryFromMultipurposeSensor():
                path_dbg |= 0x00000040
                if from_node in self._layout.my_multipurpose_sensors:
                    path_dbg |= 0x00000080
                    self.gt_sh_telemetry_from_multipurpose_sensor_received(
                        from_node, message.Payload
                    )
            case GtDriverBooleanactuatorCmd():
                path_dbg |= 0x00000100
                if from_node in self._layout.my_boolean_actuators:
                    path_dbg |= 0x00000200
                    self.gt_driver_booleanactuator_cmd_record_received(
                        from_node, message.Payload
                    )
            case _:
                raise ValueError(
                    f"There is no handler for mqtt message payload type [{type(message.Payload)}]"
                )
        self._logger.path("--Scada2._derived_process_message  path:0x%08X", path_dbg)

    # TODO: Clean this up
    # noinspection PyProtectedMember
    def log_subscriptions(self, tag=""):
        if self._logger.lifecycle_enabled:
            s = f"Scada2 subscriptions: [{tag}]]\n"
            for client in self._mqtt_clients._clients:
                s += f"\t{client}\n"
                for subscription in self._mqtt_clients._clients[client]._subscriptions:
                    s += f"\t\t[{subscription}]\n"
            self._logger.lifecycle(s)

    def _derived_process_mqtt_message(
        self, message: Message[MQTTReceiptPayload], decoded: Any
    ):
        self._logger.path("++Scada2._derived_process_mqtt_message %s", message.Payload.message.topic)
        path_dbg = 0
        if message.Payload.client_name != self.GRIDWORKS_MQTT:
            raise ValueError(
                f"There are no messages expected to be received from [{message.Payload.client_name}] mqtt broker. "
                f"Received\n\t topic: [{message.Payload.message.topic}]"
            )
        match decoded.Payload:
            case GtDispatchBoolean():
                path_dbg |= 0x00000001
                self._boolean_dispatch_received(decoded.Payload)
            case GtShCliAtnCmd():
                path_dbg |= 0x00000002
                self._gt_sh_cli_atn_cmd_received(decoded.Payload)
            case GtTelemetry():
                path_dbg |= 0x00000004
                self._process_telemetry(message, decoded.Payload)
            case ScadaDBG():
                path_dbg |= 0x00000008
                self._process_scada_dbg(decoded.Payload)
            case _:
                raise ValueError(
                    f"There is no handler for mqtt message payload type [{type(decoded.Payload)}]\n"
                    f"Received\n\t topic: [{message.Payload.message.topic}]"
                )
        self._logger.path("--Scada2._derived_process_mqtt_message  path:0x%08X", path_dbg)

    def _process_telemetry(self, message: Message, decoded: GtTelemetry):
        from_node = self._layout.node(message.Header.Src)
        if from_node in self._layout.my_simple_sensors:
            self._data.recent_simple_values[from_node].append(decoded.Value)
            self._data.recent_simple_read_times_unix_ms[from_node].append(
                decoded.ScadaReadTimeUnixMs
            )
            self._data.latest_simple_value[from_node] = decoded.Value

    def _boolean_dispatch_received(
        self, payload: GtDispatchBoolean
    ) -> ScadaCmdDiagnostic:
        """This is a dispatch message received from the atn. It is
        honored whenever DispatchContract with the Atn is live."""
        if not self.scada_atn_fast_dispatch_contract_is_alive:
            return ScadaCmdDiagnostic.IGNORING_ATN_DISPATCH
        return self._process_boolean_dispatch(payload)

    def _process_boolean_dispatch(
        self, payload: GtDispatchBoolean
    ) -> ScadaCmdDiagnostic:
        ba = self._layout.node(payload.AboutNodeAlias)
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        self._communicators[ba.alias].process_message(
            GtDispatchBooleanLocalMessage(
                src=self.name, dst=ba.alias, relay_state=payload.RelayState
            )
        )
        return ScadaCmdDiagnostic.SUCCESS

    def _set_relay_state(self, ba: ShNode, on: bool):
        if not isinstance(ba.component, BooleanActuatorComponent):
            return ScadaCmdDiagnostic.DISPATCH_NODE_NOT_BOOLEAN_ACTUATOR
        self.send_threadsafe(
            GtDispatchBooleanLocalMessage(
                src=self._layout.home_alone_node.alias, dst=ba.alias, relay_state=int(on)
            )
        )
        return ScadaCmdDiagnostic.SUCCESS

    def turn_on(self, ba: ShNode) -> ScadaCmdDiagnostic:
        return self._set_relay_state(ba, True)

    def turn_off(self, ba: ShNode) -> ScadaCmdDiagnostic:
        return self._set_relay_state(ba, False)

    def _gt_sh_cli_atn_cmd_received(self, payload: GtShCliAtnCmd):
        if payload.SendSnapshot is not True:
            return
        self._publish_to_gridworks(self._data.make_snaphsot_payload())

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

    def gs_pwr_received(self, payload: GsPwr):
        """The highest priority of the SCADA, from the perspective of the electric grid,
        is to report power changes as quickly as possible (i.e. milliseconds matter) on
        any asynchronous change more than x% (probably 2%).

        There is a single meter measuring all power getting reported - this is in fact
        what is Atomic (i.e. cannot be divided further) about the AtomicTNode. The
        asynchronous change calculation is already made in the power meter code. This
        function just passes through the result.

        The allocation to separate metered nodes is done ex-poste using the multipurpose
        telemetry data."""

        self._publish_to_gridworks(payload, QOS.AtMostOnce)
        self._data.latest_total_power_w = self.GS_PWR_MULTIPLIER * payload.Power

    def gt_sh_telemetry_from_multipurpose_sensor_received(
        self, from_node: ShNode, payload: GtShTelemetryFromMultipurposeSensor
    ):
        if from_node in self._layout.my_multipurpose_sensors:
            about_node_alias_list = payload.AboutNodeAliasList
            for idx, about_alias in enumerate(about_node_alias_list):
                if about_alias not in self._layout.nodes:
                    raise Exception(
                        f"alias {about_alias} in payload.AboutNodeAliasList not a recognized ShNode!"
                    )
                tt = TelemetryTuple(
                    AboutNode=self._layout.node(about_alias),
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

    def gt_telemetry_received(self, from_node: ShNode, payload: GtTelemetry):
        self._data.recent_simple_values[from_node].append(payload.Value)
        self._data.recent_simple_read_times_unix_ms[from_node].append(
            payload.ScadaReadTimeUnixMs
        )
        self._data.latest_simple_value[from_node] = payload.Value

    def gt_driver_booleanactuator_cmd_record_received(
        self, from_node: ShNode, payload: GtDriverBooleanactuatorCmd
    ):
        """The boolean actuator actor reports when it has sent an actuation command
        to its driver. We add this to information to be sent up in the 5 minute status
        package.

        This is different than reporting a _reading_ of the state of the
        actuator. Note that a reading of the state of the actuator may not mean the relay
        is in the read position. For example, the NCD relay requires two power sources - one
        from the Pi and one a lowish DC voltage from another plug (12 or 24V). If the second
        power source is off, the relay will still report being on when it is actually off.

        Note also that the thing getting actuated (for example the boost element in the water
        tank) may not be getting any power because of another relay in series. For example, we
        can throw a large 240V breaker in the test garage and the NCD relay will actuate without
        the boost element turning on. Or the element could be burned out.

        So measuring the current and/or power of the thing getting
        actuated is really the best test."""

        if from_node not in self._layout.my_boolean_actuators:
            raise Exception(
                "boolean actuator command records must come from boolean actuator"
            )
        if from_node.alias != payload.ShNodeAlias:
            raise Exception("Command record must come from the boolean actuator actor")
        self._data.recent_ba_cmds[from_node].append(payload.RelayState)
        self._data.recent_ba_cmd_times_unix_ms[from_node].append(
            payload.CommandTimeUnixMs
        )

    def local_boolean_dispatch_received(
        self, payload: GtDispatchBooleanLocal
    ) -> ScadaCmdDiagnostic:
        """This will be a message from HomeAlone, honored when the DispatchContract
        with the Atn is not live."""
        if self.scada_atn_fast_dispatch_contract_is_alive:
            return ScadaCmdDiagnostic.IGNORING_HOMEALONE_DISPATCH
        return self._process_boolean_dispatch(
            typing.cast(GtDispatchBoolean, payload)
        )

    def _process_mqtt_suback(self, message: Message[MQTTSubackPayload]):
        if message.Payload.num_pending_subscriptions == 0:
            for message_id in self._event_persister.pending():
                match self._event_persister.retrieve(message_id):
                    case Ok(content):
                        self._publish_to_gridworks(
                            json.loads(content.decode("utf-8")),
                            AckRequired=True
                        )
                    case Err(problems):
                        self._logger.error(problems)
                        raise ValueError(str(problems))
        super()._process_mqtt_suback(message)

    def _process_scada_dbg(self, dbg: ScadaDBG):
        self._logger.path("++_process_scada_dbg")
        path_dbg = 0
        count_dbg = 0
        for logger_name in ["message_summary", "lifecycle", "comm_event"]:
            requested_level = getattr(dbg.Levels, logger_name)
            if requested_level > -1:
                path_dbg |= 0x00000001
                count_dbg += 1
                logger = getattr(self._logger, logger_name + "_logger")
                old_level = logger.getEffectiveLevel()
                logger.setLevel(requested_level)
                self._logger.debug(
                    "%s logger level %s -> %s",
                    logger_name,
                    old_level,
                    logger.getEffectiveLevel()
                )
        match dbg.Command:
            case ScadaDBGCommands.show_subscriptions:
                path_dbg |= 0x00000002
                self.log_subscriptions("message")
            case _:
                path_dbg |= 0x00000004
        self.generate_event(ScadaDBGEvent(Command=dbg, Path=f"0x{path_dbg:08X}", Count=count_dbg, Msg=""))
        self._logger.path("--_process_scada_dbg  path:0x%08X  count:%d", path_dbg, count_dbg)
